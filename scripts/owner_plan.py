"""Owner-PDF revision: semantic, integer-mm room-first plan and exact readback."""
from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as E,math,csv,os
from design import ROOT,NS,mm,area,rect_union,sub,edges,tag,text,drawrect,ftstr
from check_routes import components,contain

RUN=ROOT/'revisions/owner-brief-v2'
PDF=ROOT/'Portal Earth Ship Project Management Plan.pdf'
BRIEF_HASH='f2987055dd351fad8ba9ab73ac2e5c406732d974d67c367d332e75b65f0b001e'
SKILL=Path(os.environ.get('ROOM_FIRST_SKILL','C:/Users/shaun/.codex/skills/room-first-building-study'))
def us_profile():
    sys.path.insert(0,str(SKILL/'scripts'))
    from building_study.framing import profile
    return profile('us').to_dict()
def wallband(e,lo=None,hi=None):
    t=e['thickness'];a=e['at'];lo=e['lo'] if lo is None else lo;hi=e['hi'] if hi is None else hi
    if e['negative'] is None:l,h=a,a+t
    elif e['positive'] is None:l,h=a-t,a
    else:l,h=a-t//2,a+t-t//2
    return (lo,l,hi,h) if e['axis']=='x' else (l,lo,h,hi)
def compose(name,width,depth):
    w,d=mm(width),mm(depth);x1,x2=round(w*.4),round(w*.68);rear=d-mm(10)
    spaces={'Living / sleeping':(0,0,x1,d),'Kitchen / dining':(x1,0,x2,rear),'Bathroom':(x1,rear,x1+mm(10),d),'Plant / laundry':(x1+mm(10),rear,x1+mm(16),d),'Service circulation':(x1+mm(16),rear,x2,d),'Garden':(x2,0,w,d)}
    ed=edges(spaces)
    for e in ed:
        e['thickness']=457 if None in (e['negative'],e['positive']) else 152 if 'Garden' in (e['negative'],e['positive']) else 114
        e['kind']='virtual' if {e['negative'],e['positive']}=={'Kitchen / dining','Service circulation'} else 'garden-screen' if None not in (e['negative'],e['positive']) and 'Garden' in (e['negative'],e['positive']) else 'retaining' if None in (e['negative'],e['positive']) else 'partition'
    ops=[]
    def opening(room,axis,at,center,width_ft,kind,other=None,sill=0,head=2438):
        lo=round(center-mm(width_ft)/2);hi=lo+mm(width_ft)
        hosts=[e for e in ed if room in (e['negative'],e['positive']) and other in (e['negative'],e['positive']) and e['axis']==axis and e['at']==at and e['lo']<=lo<hi<=e['hi']]
        assert len(hosts)==1,(room,kind,hosts)
        ops.append(dict(id=f'O{len(ops)+1:02d}',room=room,host=hosts[0]['id'],lo=lo,hi=hi,kind=kind,sill=sill,head=head,leaf_mm=914.4 if kind=='door' else 0,nominal='36 x 84 in door; 40 x 88 in rough reservation' if kind=='door' else 'supplier-designed opening'))
    opening('Living / sleeping','y',x1,mm(6),6,'portal','Kitchen / dining')
    opening('Bathroom','x',rear,x1+mm(4),10/3,'door','Kitchen / dining',head=2235)
    opening('Plant / laundry','x',rear,x1+mm(13),10/3,'door','Kitchen / dining',head=2235)
    opening('Garden','y',x2,mm(6),8,'sliding','Kitchen / dining')
    for room,center in [('Living / sleeping',mm(8)),('Kitchen / dining',x1+round((x2-x1)*.72)),('Garden',w-mm(6))]:opening(room,'x',0,center,10/3,'door',head=2235)
    opening('Living / sleeping','x',0,mm(23),10,'window',sill=610,head=2438)
    opening('Kitchen / dining','x',0,x1+mm(6),4,'window',sill=914,head=2438)
    opening('Garden','x',0,x2+mm(9),10,'window',sill=152,head=2743)
    walls=rect_union([wallband(e) for e in ed if e['kind']!='virtual'],clip=[(0,0,w,d)])
    fixtures=[]
    def fixture(id,room,r,kind,height):fixtures.append(dict(id=id,room=room,rect=[mm(v) if type(v) is float else v for v in r],kind=kind,height=height))
    fixture('king-bed','Living / sleeping',(mm(9),d-mm(10),mm(9)+1930,d-mm(10)+2032),'bed',610)
    fixture('sofa','Living / sleeping',(x1-mm(18),mm(14),x1-mm(10),mm(17)),'sofa',850)
    fixture('dining-table','Kitchen / dining',(x1+mm(4),mm(5),x1+mm(10),mm(8)),'table',762)
    fixture('kitchen-counter','Kitchen / dining',(x1+mm(14),rear-mm(7),x2-mm(1),rear-mm(5)),'cabinet',914)
    fixture('shower','Bathroom',(x1+mm(1),d-mm(5.5),x1+mm(4),d-mm(2.5)),'shower',100)
    fixture('toilet','Bathroom',(x1+mm(6),d-mm(4),x1+mm(7.5),d-mm(2)),'toilet',430)
    fixture('vanity','Bathroom',(x1+mm(6),rear+mm(2),x1+mm(9),rear+mm(4)),'cabinet',864)
    fixture('mechanical-reservation','Plant / laundry',(x1+mm(10.5),d-mm(4),x1+mm(15.5),d-mm(2)),'plant',2134)
    fixture('north-planter','Garden',(x2+mm(4),d-mm(7),w-mm(4),d-mm(3)),'planter',610)
    fixture('central-planter','Garden',(x2+mm(6),mm(10),w-mm(8),mm(14)),'planter',610)
    return dict(name=name,width=w,depth=d,spaces=spaces,edges=ed,openings=ops,wall_cells=walls,fixtures=fixtures,roof=[dict(id='opaque',rect=[-305,-305,w//2,d+305]),dict(id='polycarbonate',rect=[w//2,-305,w+305,d+305])],brief_sha256=BRIEF_HASH,roof_pitch=.10,low_wall_height_mm=3048,beam_width_in=5.125,beam_depth_in=18,beam_spacing_ft=8,framing_profile=us_profile())
def write_svg(m):
    w,d=m['width'],m['depth'];root=E.Element('{'+NS+'}svg',dict(width='1600',height='800',viewBox=f'-1000 -2400 {mm(106)} {d+mm(20)}'))
    meta=tag(root,'metadata',id='owner-contract');meta.text=json.dumps({k:m[k] for k in ['name','brief_sha256','roof_pitch','low_wall_height_mm','beam_width_in','beam_depth_in','beam_spacing_ft','framing_profile']})
    drawrect(root,(-1000,-2400,mm(106)-1000,d+mm(20)-2400),fill='#faf7ef')
    text(root,0,-1700,'OWNER BRIEF / '+m['name'],size=440,font_family='Arial',fill='#233d36',font_weight='bold')
    text(root,0,-1100,'2,500 sf gross including garden | One rectangle | Single transverse glulam span | Concept only',size=250,font_family='Arial')
    text(root,0,-600,'NORTH UP · all dimensions feet/inches · 18 in exterior reservation · 10 ft low roof datum + 10% slope',size=220,font_family='Arial')
    g=tag(root,'g',id='owner-geometry',transform=f'translate(0 {d}) scale(1 -1)')
    fp=tag(g,'g',id='footprint-source',display='none');drawrect(fp,(0,0,w,d))
    sg=tag(g,'g',id='spaces-source');colors=['#d8c5a3','#eadcb8','#bdd5d8','#d0dae0','#e7dfc5','#c4d4b3']
    for i,(n,r) in enumerate(m['spaces'].items()):drawrect(sg,r,data_name=n,fill=colors[i])
    eg=tag(g,'g',id='shared-boundaries',display='none')
    for e in m['edges']:tag(eg,'line',id=e['id'],**{'data_'+k:str(v) if v is not None else '' for k,v in e.items() if k!='id'})
    wg=tag(g,'g',id='wall-cells',fill='#344b40')
    for r in m['wall_cells']:drawrect(wg,r)
    for e in m['edges']:
        if e['kind']=='garden-screen':drawrect(g,wallband(e),fill='#6faaa9')
    em={e['id']:e for e in m['edges']};og=tag(g,'g',id='opening-source')
    for o in m['openings']:
        e=em[o['host']];drawrect(og,wallband(e,o['lo'],o['hi']),id=o['id'],fill='#faf7ef',**{'data_'+k:str(v) for k,v in o.items() if k!='id'})
        if o['kind']=='door':
            sign=1 if e['positive']==o['room'] else -1;face=e['at']+sign*(e['thickness'] if None in (e['negative'],e['positive']) else e['thickness']//2);hinge=o['lo']+51;s=914
            if e['axis']=='x':
                tag(og,'line',x1=hinge,y1=face,x2=hinge,y2=face+sign*s,stroke='#986240',stroke_width=35)
                tag(og,'path',d=f'M {hinge+s} {face} A {s} {s} 0 0 {1 if sign>0 else 0} {hinge} {face+sign*s}',fill='none',stroke='#986240',stroke_width=22)
        elif o['kind'] in ['window','sliding']:drawrect(g,wallband(e,o['lo'],o['hi']),fill='#81b4bd',fill_opacity='.55')
    fg=tag(g,'g',id='fixtures-source')
    for f in m['fixtures']:drawrect(fg,f['rect'],id=f['id'],data_room=f['room'],data_kind=f['kind'],data_height=f['height'],fill='#71925c' if f['kind']=='planter' else '#f4efe3',stroke='#9a8a70',stroke_width=20)
    rg=tag(g,'g',id='roof-source',display='none')
    for r in m['roof']:drawrect(rg,r['rect'],id=r['id'])
    # Roof split overlay remains legible without hiding the furnished plan.
    tag(g,'line',x1=w//2,x2=w//2,y1=0,y2=d,stroke='#a26635',stroke_width=45,stroke_dasharray='150 100')
    for n,(a,b,c,h) in m['spaces'].items():
        ar=area(sub([(a,b,c,h)],m['wall_cells']))/92903.04
        text(root,(a+c)/2,d-(b+h)/2,n,size=225,font_family='Arial',text_anchor='middle',fill='#20382f',font_weight='bold')
        text(root,(a+c)/2,d-(b+h)/2+320,f'{ar:.0f} sf clear',size=180,font_family='Arial',text_anchor='middle')
    for i,(a,b,label) in enumerate([(0,round(w*.4),'1,000 sf living/sleeping gross'),(round(w*.4),round(w*.68),'700 sf service gross'),(round(w*.68),w,'800 sf garden gross')]):
        text(root,(a+b)/2,d+550,label,size=220,text_anchor='middle',font_family='Arial')
    text(root,w/2,d+1100,f'{ftstr(w)} overall × {ftstr(d)} overall; roof split at {ftstr(w//2)}',size=280,text_anchor='middle',font_family='Arial')
    text(root,0,d+1700,'South daylight/escape court: main entry at service zone, second exit at living, additional garden exit.',size=220,font_family='Arial')
    text(root,0,d+2200,'50% roof = 1,250 sf before overhangs: garden + 450 sf of middle zone; bathroom remains under opaque roof.',size=220,font_family='Arial')
    text(root,0,d+2700,'Bath is enclosed; garden has a glazed humidity screen. Court-to-grade route and all structural sizes remain unverified.',size=220,font_family='Arial')
    text(root,0,d+3200,'NOT FOR CONSTRUCTION · Opt-out / water / septic approvals are assumptions, not verified evidence.',size=220,font_family='Arial',fill='#9a5738')
    p=RUN/'plans'/f'{m["name"]}.svg';p.parent.mkdir(parents=True,exist_ok=True);E.ElementTree(root).write(p,encoding='utf-8',xml_declaration=True);return p
def read_owner(path):
    root=E.parse(path).getroot();find=lambda id:root.find(f'.//{{{NS}}}g[@id="{id}"]')
    def rect(e):
        a,b,w,d=[int(e.get(k)) for k in ['x','y','width','height']];return (a,b,a+w,b+d)
    m=json.loads(root.find(f'{{{NS}}}metadata').text);fp=[rect(e) for e in find('footprint-source')];m['width'],m['depth']=fp[0][2:]
    assert m['brief_sha256']==BRIEF_HASH and m['framing_profile']['system']=='us'
    for key,value in [('stud_mm',38.1),('interior_depth_mm',88.9),('stud_spacing_mm',406.4),('rafter_spacing_mm',609.6)]:assert abs(m['framing_profile'][key]-value)<1e-8,'Unsupported framing profile edit'
    assert find('owner-geometry').get('transform')==f'translate(0 {m["depth"]}) scale(1 -1)'
    for id in ['spaces-source','footprint-source','shared-boundaries','wall-cells','opening-source','fixtures-source','roof-source']:assert not any('transform' in s.attrib for s in find(id).iter())
    m['spaces']={e.get('data-name'):rect(e) for e in find('spaces-source')};derived=edges(m['spaces']);m['edges']=[]
    for e,s in zip(derived,find('shared-boundaries')):
        assert e['id']==s.get('id')
        for k,v in e.items():assert str(v if v is not None else '')==s.get('data-'+k) if k!='id' else True
        e['kind']=s.get('data-kind');e['thickness']=int(s.get('data-thickness'));m['edges'].append(e)
    assert len(m['edges'])==len(derived)==len(list(find('shared-boundaries')))
    m['wall_cells']=rect_union([wallband(e) for e in m['edges'] if e['kind']!='virtual'],clip=fp)
    assert m['wall_cells']==[rect(e) for e in find('wall-cells')],'Stale derived wall geometry'
    assert area(rect_union(list(m['spaces'].values())))==area(list(m['spaces'].values()))==area(fp)
    assert rect_union(list(m['spaces'].values()))==fp
    em={e['id']:e for e in m['edges']};m['openings']=[]
    for s in find('opening-source'):
        if s.tag!='{'+NS+'}rect':continue
        o={k[5:]:v for k,v in s.attrib.items() if k.startswith('data-')};o['id']=s.get('id')
        for k in ['lo','hi','sill','head']:o[k]=int(o[k])
        o['leaf_mm']=float(o['leaf-mm'] if 'leaf-mm' in o else o['leaf_mm']);e=em[o['host']]
        assert e['lo']<=o['lo']<o['hi']<=e['hi'] and o['room'] in (e['negative'],e['positive'])
        assert rect(s)==wallband(e,o['lo'],o['hi']);m['openings'].append(o)
    m['fixtures']=[dict(id=s.get('id'),room=s.get('data-room'),kind=s.get('data-kind'),height=int(s.get('data-height')),rect=rect(s)) for s in find('fixtures-source')]
    m['roof']=[dict(id=s.get('id'),rect=rect(s)) for s in find('roof-source')]
    assert len(m['roof'])==2 and area([m['roof'][0]['rect']])==area([m['roof'][1]['rect']]),'Roof halves changed'
    assert {r['id']:r['rect'] for r in m['roof']}=={'opaque':(-305,-305,m['width']//2,m['depth']+305),'polycarbonate':(m['width']//2,-305,m['width']+305,m['depth']+305)},'Unsupported roof-domain edit'
    assert area(rect_union([r['rect'] for r in m['roof']]))==sum(area([r['rect']]) for r in m['roof'])
    m['source_sha256']=hashlib.sha256(Path(path).read_bytes()).hexdigest();m['source_path']=str(Path(path).relative_to(ROOT));return m
def validate(m):
    clear={n:sub([r],m['wall_cells']) for n,r in m['spaces'].items()};em={e['id']:e for e in m['edges']};checks=[]
    for f in m['fixtures']:assert area(sub([f['rect']],clear[f['room']]))==0,('Fixture outside room',f['id'])
    obstacles=sub(m['wall_cells'],[wallband(em[o['host']],o['lo'],o['hi']) for o in m['openings'] if o['kind']!='window'])+[f['rect'] for f in m['fixtures']]
    radius=381;free=sub([(radius,radius,m['width']-radius,m['depth']-radius)],[(a-radius,b-radius,c+radius,d+radius) for a,b,c,d in obstacles]);groups=components(free);route=None
    for o in m['openings']:
        if o['kind']=='window':continue
        e=em[o['host']];mid=(o['lo']+o['hi'])/2
        for room,sign in [(e['negative'],-1),(e['positive'],1)]:
            if room is None:continue
            face=e['at']+sign*(e['thickness'] if None in (e['negative'],e['positive']) else e['thickness']/2)
            across=face+sign*(radius+2);p=(mid,across) if e['axis']=='x' else (across,mid)
            found=[i for i,g in enumerate(groups) if contain(p,g)];assert found,('Door pad',o['id'],room)
            if route is None:route=found[0]
            assert route in found,('Disconnected route',o['id'])
        if o['kind']=='door':
            sign=1 if e['positive']==o['room'] else -1;face=e['at']+sign*(e['thickness'] if None in (e['negative'],e['positive']) else e['thickness']/2)
            hinge=o['lo']+51;rad=math.ceil(o['leaf_mm']+25);a,b=sorted([face,face+sign*rad]);box=(hinge,a,hinge+rad,b)
            assert area(sub([box],clear[o['room']]))==0,('Door swing outside',o['id'])
            other=[f['rect'] for f in m['fixtures'] if f['room']==o['room']]
            if other:assert area(rect_union([box],clip=other))==0,('Door swing fixture clash',o['id'])
        checks.append(o['id'])
    bed=next(f for f in m['fixtures'] if f['kind']=='bed');a,b,c,d=bed['rect']
    for p in [(a-radius-1,(b+d)/2),(c+radius+1,(b+d)/2),((a+c)/2,b-radius-1)]:assert contain(p,groups[route]),'Bed side/foot route blocked'
    return dict(source_sha256=m['source_sha256'],brief_sha256=m['brief_sha256'],gross_enclosed_sf=round(m['width']*m['depth']/92903.04,2),clear_floor_sf=round(sum(area(r) for r in clear.values())/92903.04,2),zone_gross_sf=[1000,700,800],covered_roof_fraction=.5,polycarbonate_fraction=.5,partition_coverage='pass',fixture_containment='pass',conservative_full_swings='pass',connected_30_in_routes_and_interior_door_pads='pass',bed_sides_and_foot='pass',checked_openings=checks,limits=['Concept geometry, not site survey or structural/code approval.','Gross zones include walls; clear room areas are smaller.','Daylight/thermal/glazing, private bath ventilation and garden humidity require professional sizing.','Exterior court, grade access, escape hardware and product rough openings remain reservations.'])
def main():
    for name,w,d in [('C1-owner-linear-100x25',100,25),('C2-owner-linear-83x30',2500/30,30)]:
        m=compose(name,w,d);path=write_svg(m);m=read_owner(path);receipt=validate(m)
        path.with_name(path.stem+'-validation.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
        with path.with_name(path.stem+'-rooms.csv').open('w',newline='',encoding='utf-8-sig') as f:
            wr=csv.writer(f);wr.writerow(['Room / use','Gross module sf','Clear sf'])
            for n,r in m['spaces'].items():wr.writerow([n,round(area([r])/92903.04,2),round(area(sub([r],m['wall_cells']))/92903.04,2)])
        print(name,receipt['gross_enclosed_sf'],receipt['clear_floor_sf'],'PASS')
if __name__=='__main__':main()
