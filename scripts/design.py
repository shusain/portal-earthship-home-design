"""Earth Groundship study: integer-mm geometry, semantic SVG and independent checks.
Run from workspace root: python scripts/design.py
"""
from pathlib import Path
import xml.etree.ElementTree as E
import json, hashlib, csv, math

ROOT=Path(__file__).resolve().parents[1]
NS='http://www.w3.org/2000/svg'
E.register_namespace('',NS)
def mm(ft): return round(ft*304.8)
def area(rs): return sum((c-a)*(d-b) for a,b,c,d in rs)
def rect_union(rs,clip=None,exclude=()):
    allr=list(rs)+list(exclude)+(list(clip) if clip else [])
    if not allr:return []
    xs=sorted({v for r in allr for v in (r[0],r[2])});ys=sorted({v for r in allr for v in (r[1],r[3])})
    def inside(x,y,rr):return any(a<x<c and b<y<d for a,b,c,d in rr)
    cells=[]
    for a,c in zip(xs,xs[1:]):
        for b,d in zip(ys,ys[1:]):
            x,y=(a+c)/2,(b+d)/2
            if inside(x,y,rs) and (not clip or inside(x,y,clip)) and not inside(x,y,exclude):cells.append((a,b,c,d))
    # Merge cells without changing occupied domain.
    for axis in (0,1):
        changed=True
        while changed:
            changed=False
            for i,r in enumerate(cells):
                for j in range(i+1,len(cells)):
                    s=cells[j]
                    if axis==0 and r[1]==s[1] and r[3]==s[3] and (r[2]==s[0] or s[2]==r[0]):
                        t=(min(r[0],s[0]),r[1],max(r[2],s[2]),r[3])
                    elif axis==1 and r[0]==s[0] and r[2]==s[2] and (r[3]==s[1] or s[3]==r[1]):
                        t=(r[0],min(r[1],s[1]),r[2],max(r[3],s[3]))
                    else:continue
                    cells[i]=t;cells.pop(j);changed=True;break
                if changed:break
    return sorted(cells)
def sub(a,b):return rect_union(a,exclude=b)
def tag(parent,name,**attrs):return E.SubElement(parent,'{'+NS+'}'+name,{k.replace('_','-'):str(v) for k,v in attrs.items()})
def text(parent,x,y,value,size=180,**kw):
    e=tag(parent,'text',x=x,y=y,font_size=size,**kw);e.text=value;return e
def drawrect(p,r,**kw):
    a,b,c,d=r;return tag(p,'rect',x=a,y=b,width=c-a,height=d-b,**kw)
def ftstr(v):
    inches=round(v/25.4);return f'{inches//12}\u2032 {inches%12}\u2033'
def edges(spaces):
    out=[];rs=list(spaces.values());xs=sorted({v for r in rs for v in (r[0],r[2])});ys=sorted({v for r in rs for v in (r[1],r[3])})
    def owner(x,y):return next((n for n,(a,b,c,d) in spaces.items() if a<x<c and b<y<d),None)
    for axis,ats,intervals in [('x',ys,xs),('y',xs,ys)]:
        for at in ats:
            for lo,hi in zip(intervals,intervals[1:]):
                t=(lo+hi)/2
                neg,pos=(owner(t,at-0.1),owner(t,at+0.1)) if axis=='x' else (owner(at-0.1,t),owner(at+0.1,t))
                if neg!=pos:
                    key=(axis,at,neg,pos)
                    if out and out[-1]['key']==key and out[-1]['hi']==lo:out[-1]['hi']=hi
                    else:out.append(dict(key=key,axis=axis,at=at,lo=lo,hi=hi,negative=neg,positive=pos))
    for i,e in enumerate(out):e.pop('key');e['id']=f'e{i:03d}'
    return out
def band(e,thickness=None):
    ext=e['negative'] is None or e['positive'] is None
    t=thickness or (305 if ext else 114)
    at=e['at'];l,h=e['lo'],e['hi']
    if ext:a,b=(at,at+t) if e['negative'] is None else (at-t,at)
    else:a,b=at-t//2,at+(t-t//2)
    return (l,a,h,b) if e['axis']=='x' else (a,l,b,h)
def make_scheme(name,w,h,southcuts,northcuts,depth,private):
    W,H=mm(w),mm(h);hy0=mm(depth);hy1=hy0+mm(4.5)
    spaces={}
    for cuts,y0,y1 in [(southcuts,0,hy0),(northcuts,hy1,H)]:
        for n,x0,x1 in cuts:spaces[n]=(mm(x0),y0,mm(x1),y1)
    spaces['Gallery']=(0,hy0,mm(private),hy1);spaces['Suite vestibule']=(mm(private),hy0,W,hy1)
    ed=edges(spaces);virtual=[];openings=[]
    public={'Living','Kitchen','Dining','Gallery'}
    for e in ed:
        pair={e['negative'],e['positive']};ext=None in pair
        if not ext and pair<=public:virtual.append(e['id']);continue
        if not ext and pair=={'Gallery','Suite vestibule'}:
            virtual.append(e['id']);continue
        if not ext and ('Gallery' in pair or 'Suite vestibule' in pair):
            room=next(x for x in pair if x not in ('Gallery','Suite vestibule'))
            width=mm(3);mid=(e['lo']+e['hi'])//2
            # Keep doors clear of side walls and preserve furnishing zones.
            lo=mid-width//2
            openings.append(dict(id=f'D{len(openings)+1:02}',host=e['id'],kind='door',room=room,lo=lo,hi=lo+width,sill=0,head=2134,hinge='low',swing_into=room))
    def extopening(room,axis,at,mid,width,kind,sill=0,head=2134):
        es=[e for e in ed if room in (e['negative'],e['positive']) and None in (e['negative'],e['positive']) and e['axis']==axis and e['at']==at and e['lo']<=mm(mid)-mm(width)/2 and e['hi']>=mm(mid)+mm(width)/2]
        assert len(es)==1,(room,es)
        e=es[0];lo=mm(mid)-mm(width)//2
        openings.append(dict(id=f'{"W" if kind=="window" else "D"}{len(openings)+1:02}',host=e['id'],kind=kind,room=room,lo=lo,hi=lo+mm(width),sill=sill,head=head,hinge='low',swing_into=room))
    extopening('Living','x',0,5,3,'door')
    extopening('Gallery','y',0,depth+2.25,3,'door')
    extopening('Living','x',0,12,6,'window',610,2438)
    for n in ['Bedroom 2','Bedroom 3','Primary bedroom']:
        a,b,c,d=spaces[n];extopening(n,'x',0,(a+c)/609.6,4,'window',762,2286)
    active=[e for e in ed if e['id'] not in virtual]
    gross=(0,0,W,H)
    walls=rect_union([band(e) for e in active],clip=[gross])
    clear={n:sub([r],walls) for n,r in spaces.items()}
    # Physical furnishing reservations, all expressed in actual source geometry.
    fixtures=[]
    for n in ['Bedroom 2','Bedroom 3','Primary bedroom']:
        a,b,c,d=spaces[n];bw=mm(6 if n=='Primary bedroom' else 5);bd=mm(6.667)
        fixtures.append(dict(id=n.replace(' ','_')+'_bed',room=n,rect=[a+mm(2.75),b+mm(4),a+mm(2.75)+bw,b+mm(4)+bd],height=610,kind='bed'))
        if n!='Primary bedroom':fixtures.append(dict(id=n.replace(' ','_')+'_wardrobe',room=n,rect=[c-mm(2.5),d-mm(4),c-mm(.5),d-mm(.75)],height=2134,kind='wardrobe'))
    for n in ['Kitchen','Bath','Primary bath','Laundry','Mechanical / pantry','Walk-in closet']:
        if n not in spaces:continue
        a,b,c,d=spaces[n]
        fixtures.append(dict(id=n.replace(' ','_')+'_counter',room=n,rect=[a+mm(1),d-mm(3),c-mm(1),d-mm(1)],height=914,kind='cabinet'))
        if 'bath' in n.lower():
            fixtures.extend([dict(id=n+'_shower',room=n,rect=[a+mm(.5),b+mm(5),a+mm(3.5),b+mm(8)],height=100,kind='shower'),dict(id=n+'_wc',room=n,rect=[c-mm(3),b+mm(5),c-mm(1.5),b+mm(7.5)],height=420,kind='toilet')])
    a,b,c,d=spaces['Living'];fixtures.append(dict(id='sofa',room='Living',rect=[a+mm(2),b+mm(8),a+mm(10),b+mm(11)],height=850,kind='sofa'))
    a,b,c,d=spaces['Dining'];fixtures.append(dict(id='dining_table',room='Dining',rect=[a+mm(2),b+mm(5),c-mm(2),b+mm(8)],height=760,kind='table'))
    return dict(schema='earth-groundship-svg-v1',id=name,units='mm',width=W,depth=H,spaces=spaces,edges=ed,virtual=virtual,openings=openings,wall_cells=walls,clear=clear,fixtures=fixtures)
def emit_svg(m):
    W,H=m['width'],m['depth'];root=E.Element('{'+NS+'}svg',dict(viewBox=f'-1300 -1800 {mm(69)+2600} {mm(42)+4200}',width='1500',height='1050'))
    meta=tag(root,'metadata',id='contract');meta.text=json.dumps(dict(schema=m['schema'],id=m['id'],units='mm',height_mm=2743,exterior_wall_mm=305,partition_mm=114))
    tag(root,'rect',x=-1300,y=-1800,width=mm(69)+2600,height=mm(42)+4200,fill='#faf7ef')
    text(root,0,-1000,'EARTH GROUNDSHIP / '+m['id'],size=440,fill='#243a35',font_family='Arial',font_weight='bold')
    text(root,0,-450,'Single-story earth-bermed ranch | Concept review | Dimensions in feet / inches',size=230,font_family='Arial')
    g=tag(root,'g',id='geometry',transform=f'translate(0 {H}) scale(1 -1)')
    fp=tag(g,'g',id='footprint-source',display='none');drawrect(fp,(0,0,W,H),id='envelope')
    sg=tag(g,'g',id='spaces-source')
    colors=['#e6d3ac','#c4d7cb','#c4d7cb','#b7cabb','#f0d9b3','#ebd9bb','#d0dbe1','#c1d9dc','#d0dbe1','#c1d9dc','#dcd3c5','#f4e7cf','#e1d5c3']
    for i,(n,r) in enumerate(m['spaces'].items()):drawrect(sg,r,id='space-'+str(i),data_name=n,fill=colors[i%len(colors)])
    eg=tag(g,'g',id='shared-boundaries',display='none')
    for e in m['edges']:tag(eg,'line',id=e['id'],data_axis=e['axis'],data_at=e['at'],data_lo=e['lo'],data_hi=e['hi'],data_negative=e['negative'] or '',data_positive=e['positive'] or '',data_virtual=str(e['id'] in m['virtual']).lower())
    wg=tag(g,'g',id='wall-cells',fill='#37463f')
    for i,r in enumerate(m['wall_cells']):drawrect(wg,r,id='wall-'+str(i))
    og=tag(g,'g',id='opening-source');emap={e['id']:e for e in m['edges']}
    for o in m['openings']:
        e=emap[o['host']];r=band({**e,'lo':o['lo'],'hi':o['hi']});attrs={'data_'+k:str(v) for k,v in o.items() if k!='id'}
        drawrect(og,r,id=o['id'],fill='#faf7ef',**attrs)
        if o['kind']=='window':
            if e['axis']=='x':tag(og,'line',x1=o['lo'],x2=o['hi'],y1=e['at']+153,y2=e['at']+153,stroke='#4595a1',stroke_width=65)
        else:
            # Swing quarter-disc opens toward room at its finished wall face.
            rroom=m['spaces'][o['room']];sign=1 if e['positive']==o['room'] else -1;t=305 if None in (e['negative'],e['positive']) else 57
            face=e['at']+sign*t;lo,hi=o['lo'],o['hi'];s=hi-lo
            if e['axis']=='x':
                tag(og,'line',x1=lo,y1=face,x2=lo,y2=face+sign*s,stroke='#865e3e',stroke_width=35)
                tag(og,'path',d=f'M {hi} {face} A {s} {s} 0 0 {1 if sign>0 else 0} {lo} {face+sign*s}',fill='none',stroke='#865e3e',stroke_width=20)
            else:
                tag(og,'line',x1=face,y1=lo,x2=face+sign*s,y2=lo,stroke='#865e3e',stroke_width=35)
                tag(og,'path',d=f'M {face} {hi} A {s} {s} 0 0 {0 if sign>0 else 1} {face+sign*s} {lo}',fill='none',stroke='#865e3e',stroke_width=20)
    fg=tag(g,'g',id='fixtures-source')
    for f in m['fixtures']:drawrect(fg,f['rect'],id=f['id'],data_room=f['room'],data_height=f['height'],data_kind=f['kind'],fill='#f6f2e8',stroke='#998b78',stroke_width=22)
    # Labels outside the world transform, preserving readable text.
    lg=tag(root,'g',font_family='Arial',text_anchor='middle',fill='#203c37')
    for n,r in m['spaces'].items():
        a,b,c,d=r;cy=H-(b+d)/2
        text(lg,(a+c)/2,cy,n,size=195,font_weight='bold')
        cr=m['clear'][n];ar=area(cr)/92903.04
        text(lg,(a+c)/2,cy+270,f'{ar:.0f} sf clear',size=165)
        if n not in ('Gallery','Suite vestibule'):
            rr=max(cr,key=lambda q:(q[2]-q[0])*(q[3]-q[1]));text(lg,(a+c)/2,cy+500,f'{ftstr(rr[2]-rr[0])} x {ftstr(rr[3]-rr[1])}',size=150)
    text(root,W/2,H+650,f'{ftstr(W)} overall',size=270,text_anchor='middle',font_family='Arial')
    text(root,W+300,H/2,f'{ftstr(H)}',size=240,font_family='Arial',transform=f'rotate(90 {W+300} {H/2})')
    text(root,0,H+1200,'SOUTH / WALK-OUT YARD: entry + bedroom escape windows; no greenhouse across escape paths.',size=210,font_family='Arial')
    text(root,0,H+1600,'NORTH: uphill berm + waterproofed retaining wall; roof drains to south. North is up.',size=210,font_family='Arial')
    text(root,0,H+2000,'12 in total exterior / 4.5 in partitions; 9 ft clear ceilings. Structural sizes are study inputs.',size=210,font_family='Arial')
    text(root,0,H+2400,'NOT FOR CONSTRUCTION. Parcel, survey, geotechnical, structural and permit review remain open.',size=210,font_family='Arial',fill='#944e30')
    path=ROOT/'plans'/f'{m["id"]}.svg';E.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
    return path
def read_svg(path):
    """Read actual named SVG geometry; regenerate and compare derived walls."""
    root=E.parse(path).getroot();find=lambda name:root.find(f'.//{{{NS}}}g[@id="{name}"]')
    def rect(e):
        a,b,w,h=(int(e.get(k)) for k in ['x','y','width','height']);return (a,b,a+w,b+h)
    md=json.loads(root.find(f'{{{NS}}}metadata').text)
    envelope=rect(list(find('footprint-source'))[0])
    assert find('geometry').get('transform')==f'translate(0 {envelope[3]}) scale(1 -1)','Unsupported world transform'
    assert not any('transform' in e.attrib for g in ['spaces-source','footprint-source','shared-boundaries','opening-source','wall-cells','fixtures-source'] for e in find(g).iter())
    spaces={e.get('data-name'):rect(e) for e in find('spaces-source')};fp=[rect(e) for e in find('footprint-source')]
    ed=edges(spaces);stored=list(find('shared-boundaries'));assert len(ed)==len(stored)
    virtual=[]
    for e,s in zip(ed,stored):
        assert e['id']==s.get('id')
        for k in ['axis','at','lo','hi','negative','positive']:assert str(e[k] if e[k] is not None else '')==s.get('data-'+k)
        if s.get('data-virtual')=='true':virtual.append(e['id'])
    walls=rect_union([band(e) for e in ed if e['id'] not in virtual],clip=fp)
    assert walls==[rect(e) for e in find('wall-cells')],'Stale derived wall cells'
    assert area(rect_union(list(spaces.values())))==area(list(spaces.values()))==area(fp),'Coverage or overlap'
    assert rect_union(list(spaces.values()))==fp
    ops=[];emap={e['id']:e for e in ed}
    for s in find('opening-source'):
        if s.tag!='{'+NS+'}rect':continue
        o={k[5:]:v for k,v in s.attrib.items() if k.startswith('data-')};o['id']=s.get('id')
        for k in ['lo','hi','sill','head']:o[k]=int(o[k])
        e=emap[o['host']];assert e['lo']<=o['lo']<o['hi']<=e['hi']
        assert o['room'] in (e['negative'],e['positive'])
        assert rect(s)==band({**e,'lo':o['lo'],'hi':o['hi']})
        ops.append(o)
    fixtures=[dict(id=s.get('id'),room=s.get('data-room'),rect=rect(s),height=int(s.get('data-height')),kind=s.get('data-kind')) for s in find('fixtures-source')]
    return dict(id=md['id'],spaces=spaces,edges=ed,virtual=virtual,wall_cells=walls,openings=ops,fixtures=fixtures,width=fp[0][2],depth=fp[0][3],source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),clear={n:sub([r],walls) for n,r in spaces.items()})
def validate(m):
    checks=[];emap={e['id']:e for e in m['edges']};graph={n:set() for n in m['spaces']};graph['OUTSIDE']=set()
    def connect(a,b):
        a=a or 'OUTSIDE';b=b or 'OUTSIDE';graph[a].add(b);graph[b].add(a)
    for e in m['edges']:
        if e['id'] in m['virtual']:connect(e['negative'],e['positive'])
    obstacles={n:[f['rect'] for f in m['fixtures'] if f['room']==n] for n in m['spaces']}
    for f in m['fixtures']:
        assert area(sub([f['rect']],m['clear'][f['room']]))==0,('Fixture outside clear room',f['id'])
    for o in m['openings']:
        if o['kind']!='door':continue
        e=emap[o['host']];connect(e['negative'],e['positive'])
        sign=1 if e['positive']==o['room'] else -1;t=305 if None in (e['negative'],e['positive']) else 57;face=e['at']+sign*t
        # Conservative square bounding full 90 degree swing, plus 1 inch margin.
        radius=o['hi']-o['lo']+25;l,h=sorted([face,face+sign*radius])
        swing=(o['lo'],l,o['lo']+radius,h) if e['axis']=='x' else (l,o['lo'],h,o['lo']+radius)
        assert area(sub([swing],m['clear'][o['room']]))==0,('Swing outside room',o['id'])
        if obstacles[o['room']]:assert area(rect_union([swing],clip=obstacles[o['room']]))==0,('Swing fixture clash',o['id'])
        checks.append(dict(opening=o['id'],full_swing_conservative_box='pass'))
    seen={'OUTSIDE'};todo=['OUTSIDE']
    while todo:
        for n in graph[todo.pop()]-seen:seen.add(n);todo.append(n)
    assert len(seen)==len(graph),'Unreachable room'
    # Private rooms cannot be through routes: remove each and check remaining public access.
    for blocked in ['Bedroom 2','Bedroom 3','Primary bedroom','Bath','Primary bath','Walk-in closet']:
        reached={'OUTSIDE'};todo=['OUTSIDE']
        while todo:
            for n in graph[todo.pop()]-reached-{blocked}:reached.add(n);todo.append(n)
        assert set(graph)-{blocked}<=reached,('Private through route',blocked)
    gross=m['width']*m['depth']/92903.04;net=sum(area(r) for r in m['clear'].values())/92903.04
    return dict(source_sha256=m['source_sha256'],gross_enclosed_sf=round(gross,2),clear_floor_sf=round(net,2),walls_sf=round(gross-net,2),fixture_containment='pass',room_coverage='pass',shared_wall_ownership='pass',door_checks=checks,access_graph='pass',private_through_routes='none',limits=['Clear area excludes full wall bands, including door thresholds; conservative finish area.','Door swing boxes verified against room walls and fixed furniture.','Walking and both-side pads are checked in the furnished routing report separately.','No structural, thermal, drainage, daylight-performance or code approval is implied.'])
def main():
    schemes=[make_scheme('A-long-ranch',64,34,[('Living',0,24),('Bedroom 2',24,36),('Bedroom 3',36,48),('Primary bedroom',48,64)],[('Kitchen',0,16),('Dining',16,24),('Mechanical / pantry',24,32),('Bath',32,40),('Laundry',40,48),('Primary bath',48,57),('Walk-in closet',57,64)],15,48),make_scheme('B-compact-ranch',58,37,[('Living',0,18),('Bedroom 2',18,30),('Bedroom 3',30,42),('Primary bedroom',42,58)],[('Kitchen',0,10),('Dining',10,18),('Mechanical / pantry',18,26),('Bath',26,34),('Laundry',34,42),('Primary bath',42,51),('Walk-in closet',51,58)],16,42)]
    receipts={}
    for m in schemes:
        p=emit_svg(m);r=read_svg(p);receipt=validate(r);receipts[m['id']]=receipt
        (ROOT/'plans'/f'{m["id"]}-validation.json').write_text(json.dumps(receipt,indent=2))
        with (ROOT/'plans'/f'{m["id"]}-rooms.csv').open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['Room','Clear area sf','Module width ft','Module depth ft'])
            for n,(a,b,c,d) in r['spaces'].items():w.writerow([n,round(area(r['clear'][n])/92903.04,2),round((c-a)/304.8,3),round((d-b)/304.8,3)])
    print(json.dumps({n:{k:v for k,v in r.items() if k in ['gross_enclosed_sf','clear_floor_sf','source_sha256']} for n,r in receipts.items()},indent=2))
if __name__=='__main__':main()
