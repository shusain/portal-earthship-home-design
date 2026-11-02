"""Exact rectilinear walking-envelope checks from the semantic source.
Clear center domains are rectangle unions; no raster sampling or door-width approval.
"""
from pathlib import Path
import json
from design import ROOT,read_svg,validate,rect_union,sub,band,area,mm

def components(rs):
    todo=set(tuple(r) for r in rs);groups=[]
    def adjacent(a,b):return ((a[2]==b[0] or b[2]==a[0]) and max(a[1],b[1])<min(a[3],b[3])) or ((a[3]==b[1] or b[3]==a[1]) and max(a[0],b[0])<min(a[2],b[2]))
    while todo:
        seed=todo.pop();q=[seed];g=[seed]
        while q:
            a=q.pop();connected={b for b in todo if adjacent(a,b)};todo-=connected;q.extend(connected);g.extend(connected)
        groups.append(g)
    return groups
def contain(p,rs):return any(a<=p[0]<=c and b<=p[1]<=d for a,b,c,d in rs)
def run(path):
    m=read_svg(path);validate(m);emap={e['id']:e for e in m['edges']};w=m['width'];h=m['depth'];radius=381
    doorcuts=[band({**emap[o['host']],'lo':o['lo'],'hi':o['hi']}) for o in m['openings'] if o['kind']=='door']
    obstacles=sub(m['wall_cells'],doorcuts)+[f['rect'] for f in m['fixtures']]
    expanded=[(a-radius,b-radius,c+radius,d+radius) for a,b,c,d in obstacles]
    free=sub([(radius,radius,w-radius,h-radius)],expanded);groups=components(free)
    # Track every room door's 30-inch-square landing on both finished sides.
    checks=[];access_group=None
    for o in m['openings']:
        if o['kind']!='door':continue
        e=emap[o['host']];mid=(o['lo']+o['hi'])//2;points=[]
        for n,sign in [(e['negative'],-1),(e['positive'],1)]:
            if n is None:continue # External grading/pads are unresolved site geometry.
            offset=305 if None in (e['negative'],e['positive']) else 57
            across=e['at']+sign*(offset+radius+1)
            p=(mid,across) if e['axis']=='x' else (across,mid)
            found=[i for i,g in enumerate(groups) if contain(p,g)];assert found,('No furnished landing',m['id'],o['id'],n,p)
            if access_group is None:access_group=found[0]
            assert access_group in found,('Disconnected walking route',o['id'],n)
            points.append(dict(room=n,center_mm=p))
        checks.append(dict(door=o['id'],both_interior_side_pads='pass',pads=points))
    # At least a 36-inch continuous lane through both circulation modules.
    hall=[]
    for n in ['Gallery','Suite vestibule']:
        a,b,c,d=m['spaces'][n];lane=(max(305,a),b+57,min(w-305,c),d-57)
        assert lane[3]-lane[1]>=914
        assert area(rect_union([lane],clip=[f['rect'] for f in m['fixtures']]))==0
        hall.append(dict(space=n,clear_width_in=round((lane[3]-lane[1])/25.4,2)))
    bedchecks=[]
    for f in m['fixtures']:
        if f['kind']!='bed':continue
        a,b,c,d=f['rect']
        for side,p in [('left',(a-radius-1,(b+d)/2)),('right',(c+radius+1,(b+d)/2)),('foot',((a+c)/2,b-radius-1))]:
            assert contain(p,groups[access_group]),('Bed access',f['id'],side)
        bedchecks.append(dict(bed=f['id'],thirty_inch_access_both_sides_and_foot='pass'))
    return dict(source_sha256=m['source_sha256'],walking_square_in=30,exact_positive_edge_connectivity='pass',door_pads=checks,hall_widths=hall,bed_access=bedchecks,limits=['30-inch square is a study envelope, not an accessibility or code compliance claim.','Door leaves are assumed held at 90 degrees for walking checks; full swings are independently checked against fixtures.','Exterior landings, yard-to-public-way connection and real door/frame clear dimensions need parcel and product details.','A 36-inch walking envelope cannot pass all nominal 36-inch source door reservations with finished hardware; accessible-route compliance is not asserted.'])
if __name__=='__main__':
    for path in [ROOT/'plans'/'A-long-ranch.svg',ROOT/'plans'/'B-compact-ranch.svg']:
        receipt=run(path);out=path.with_name(path.stem+'-routes.json');out.write_text(json.dumps(receipt,indent=2));print(path.stem,'ROUTES PASS')
