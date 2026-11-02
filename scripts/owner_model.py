"""Separate background Blender recipe for the owner-PDF three-zone revision."""
import sys,math,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from owner_plan import RUN,read_owner,validate,wallband
from design import rect_union,sub,mm,area
import bpy
from mathutils import Vector

source=RUN/'plans/C1-owner-linear-100x25.svg';m=read_owner(source);validate(m)
p=m['framing_profile'];IN=25.4;W,D=m['width'],m['depth'];P=m['roof_pitch'];COS=1/math.sqrt(1+P*P);SIN=P*COS;BASE=m['low_wall_height_mm'];BW=m['beam_width_in']*IN;BD=m['beam_depth_in']*IN
bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.name='01 Owner construction sequence';s.unit_settings.system='IMPERIAL';s.unit_settings.length_unit='FEET'
STAGES={1:'Site / court reservations',2:'Footings',3:'Subslab and slab',4:'Retaining shell',5:'Waterproofing / insulation',6:'Drainage reservation',7:'Full-span glulam',8:'Secondary wood roof frame',9:'Opaque roof half',10:'Polycarbonate roof half / joints',11:'Exterior shading and vent reservations',12:'Partitions / humidity screen / openings',13:'Interior and garden',14:'Engineered backfill context'}
collections={};components=[];mats={}
def material(name,color,transmission=0):
    a=bpy.data.materials.new(name);a.diffuse_color=(*color,1);a.use_nodes=True;bs=a.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.4
    if transmission:bs.inputs['Transmission Weight'].default_value=transmission;bs.inputs['IOR'].default_value=1.45
    return a
concrete=material('Concrete',(.54,.56,.52));wood=material('US timber',(.52,.32,.14));plaster=material('Mineral finish',(.85,.8,.67));foam=material('Insulation',(.58,.73,.67));membrane=material('Waterproofing',(.07,.12,.12));aggregate=material('Aggregate',(.35,.38,.35));earth=material('Earth / site context',(.4,.31,.19));pc=material('Polycarbonate reservation',(.62,.83,.81),.55);glass=material('Garden humidity screen',(.58,.76,.78),.7);furniture=material('Furniture context',(.64,.42,.23));leaf=material('Garden vegetation context',(.18,.36,.13));finish=material('Opaque roof finish',(.65,.7,.65))
def mesh(name,verts,ma,stage,part,quantity=None,unit='cf',status='measured',host='',thickness_in=None):
    if stage not in collections:
        c=bpy.data.collections.new(f'{stage:02d} {STAGES[stage]}');s.collection.children.link(c);collections[stage]=c
    me=bpy.data.meshes.new(name);me.from_pydata([(x/1000,y/1000,z/1000) for x,y,z in verts],[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.update()
    ob=bpy.data.objects.new(name,me);collections[stage].objects.link(ob);ob.data.materials.append(ma)
    for k,v in dict(component_id=f'V2-C{len(components)+1:05d}',part=part,stage=stage,level='single-story',assembly=part,host=host,status=status,quantity_unit=unit,source_sha256=m['source_sha256']).items():ob[k]=v
    if quantity is not None:ob['quantity']=quantity
    if thickness_in is not None:ob['thickness_in']=thickness_in
    start=(stage-1)*10+1
    for frame,hide in [(1,stage>1),(max(1,start-1),True),(start,False),(151,False)]:
        ob.hide_render=hide;ob.hide_viewport=hide;ob.keyframe_insert('hide_render',frame=frame);ob.keyframe_insert('hide_viewport',frame=frame)
    components.append(ob);return ob
def wedge(name,r,low,high,ma,stage,part,**kw):
    a,b,c,d=r;return mesh(name,[(a,b,low(b)),(c,b,low(b)),(c,d,low(d)),(a,d,low(d)),(a,b,high(b)),(c,b,high(b)),(c,d,high(d)),(a,d,high(d))],ma,stage,part,**kw)
def box(name,r,z0,z1,ma,stage,part,**kw):return wedge(name,r,lambda y:z0,lambda y:z1,ma,stage,part,**kw)
def extband(e,depth):return wallband({**e,'thickness':depth})
fp=[(0,0,W,D)];ext=[e for e in m['edges'] if e['kind']=='retaining'];internal=[e for e in m['edges'] if e['kind']=='partition'];screen=[e for e in m['edges'] if e['kind']=='garden-screen'];emap={e['id']:e for e in m['edges']}
all_ext=rect_union([wallband(e) for e in ext],clip=fp)
def openingcuts(z):return [wallband(emap[o['host']],o['lo'],o['hi']) for o in m['openings'] if o['sill']<=z<o['head']]
levels=sorted({-610,0,2743}|{o[k] for o in m['openings'] for k in ['sill','head']})
def walllayers(domain,ma,stage,part,thickness):
    for a,b in zip(levels,levels[1:]):
        if part in ['Partition lining','Exterior wall inside finish'] and b<=0:continue
        for i,r in enumerate(sub(domain,openingcuts((a+b)/2))):box(f'{part} {a}-{i}',r,a,b,ma,stage,part,thickness_in=thickness/IN)
    for i,r in enumerate(domain):wedge(part+' upper '+str(i),r,lambda y:2743,lambda y:BASE+P*y,ma,stage,part,thickness_in=thickness/IN)
foot=rect_union([(-152,-152,W+152,762),(-152,D-762,W+152,D+152),(-152,762,762,D-762),(W-762,762,W+152,D-762)])
for i,r in enumerate(foot):box('Footing '+str(i),r,-915,-610,concrete,2,'Concrete footings',unit='cy')
slab=(457,457,W-457,D-457);sf=area([slab])/92903.04
for name,z0,z1,ma,part,unit in [('Aggregate',-305,-153,aggregate,'Subslab aggregate','cy'),('Floor insulation',-153,-103,foam,'Subslab insulation','sf'),('Vapor barrier',-103,-102,membrane,'Slab vapor barrier','sf'),('Slab',-102,0,concrete,'Concrete slab','cy')]:box(name,slab,z0,z1,ma,3,part,quantity=sf if unit=='sf' else None,unit=unit)
prev=[]
for depth,ma,stage,part,th in [(12,aggregate,5,'Wall drainage/protection',12),(15,membrane,5,'Wall waterproofing',3),(117,foam,5,'Wall rigid insulation',102),(422,concrete,4,'Retaining concrete core',305),(457,plaster,12,'Exterior wall inside finish',35)]:
    region=rect_union([extband(e,depth) for e in ext],clip=fp);walllayers(sub(region,prev),ma,stage,part,th);prev=region
for i,r in enumerate([(-254,-254,W+254,-152),(-254,D+152,W+254,D+254),(-254,-152,-152,D+152),(W+152,-152,W+254,D+152)]):
    length=max(r[2]-r[0],r[3]-r[1])/304.8;box('Drain route '+str(i),r,-510,-408,membrane,6,'Footing drain reservation',quantity=length,unit='lf',status='reservation')
# One actual beam object spans north-south between perimeter bearings; no interior bearing line.
beam_x=[12*IN+i*96*IN for i in range(20) if 12*IN+i*96*IN<W-12*IN]+[W-12*IN]
beam_y0,beam_y1=-305,D+305
for i,x in enumerate(beam_x):
    bottom=[(x-BW/2,beam_y0,BASE+P*beam_y0),(x+BW/2,beam_y0,BASE+P*beam_y0),(x+BW/2,beam_y1,BASE+P*beam_y1),(x-BW/2,beam_y1,BASE+P*beam_y1)]
    verts=bottom+[(a,b-BD*SIN,c+BD*COS) for a,b,c in bottom]
    ob=mesh(f'Full-span glulam {i+1:02}',verts,wood,7,'Glulam beam reservation',quantity=(beam_y1-beam_y0)/(COS*304.8),unit='lf',status='reservation');ob['actual_section_in']=[m['beam_width_in'],m['beam_depth_in']];ob['span_axis']='north-south';ob['purchase_length_ft']=28
    for y in [305,D-305]:box(f'Beam connection reservation {i}-{y}',(x-BW/2-30,y-75,x+BW/2+30,y+75),BASE+P*y-40,BASE+P*y,membrane,7,'Beam bearing/connection reservation',quantity=1,unit='each',status='reservation')
beam_top=BD/COS;pur_depth=p['tie_depth_mm'];pur_width=p['stud_mm'];roof_base=BASE+beam_top+pur_depth/COS
for yi,y in enumerate([-305+j*p['rafter_spacing_mm'] for j in range(math.ceil((D+610)/p['rafter_spacing_mm']))]+[D+305]):
    for j,(a,c) in enumerate(zip(beam_x,beam_x[1:])):
        low=[]
        for x,v in [(a,-pur_width/2),(c,-pur_width/2),(c,pur_width/2),(a,pur_width/2)]:low.append((x,y+v*COS,BASE+P*y+beam_top+v*SIN))
        verts=low+[(x,y-pur_depth*SIN,z+pur_depth*COS) for x,y,z in low]
        ob=mesh(f'2x8 purlin {yi}-{j}',verts,wood,8,'Roof purlin 2x8',quantity=(c-a)/304.8,unit='lf');ob['actual_section_in']=[1.5,7.25];ob['grid_station_mm']=y;ob['framing_grid_role']='roof-purlin'
opaque=next(r['rect'] for r in m['roof'] if r['id']=='opaque');glazed=next(r['rect'] for r in m['roof'] if r['id']=='polycarbonate')
for name,normal,ma,part in [('Roof deck',23/32*IN,wood,'Opaque roof deck'),('Roof insulation',6*IN,foam,'Opaque roof insulation'),('Roof cover board',.5*IN,plaster,'Opaque cover board'),('Roof membrane',.060*IN,finish,'Opaque roof membrane')]:
    low=roof_base;roof_base+=normal/COS;wedge(name,opaque,lambda y,z=low:z+P*y,lambda y,z=roof_base:z+P*y,ma,9,part,quantity=area([opaque])/(92903.04*COS),unit='sf')
glaze_base=BASE+beam_top+pur_depth/COS;curb=p['collar_depth_mm']
stations=[glazed[0]+i*48*IN for i in range(math.ceil((glazed[2]-glazed[0])/(48*IN)))]+[glazed[2]]
for i,x in enumerate(stations):
    r=(x-p['stud_mm']/2,glazed[1],x+p['stud_mm']/2,glazed[3]);wedge('Glazing 2x6 seam frame '+str(i),r,lambda y:glaze_base+P*y,lambda y:glaze_base+curb/COS+P*y,wood,10,'Glazing frame 2x6',quantity=(glazed[3]-glazed[1])/(304.8*COS),unit='lf')
for i,(a,c) in enumerate(zip(stations,stations[1:])):
    r=(a+20,glazed[1],c-20,glazed[3]);wedge('PC panel reservation '+str(i),r,lambda y:glaze_base+curb/COS+P*y,lambda y:glaze_base+(curb+16)/COS+P*y,pc,10,'Polycarbonate 5/8 in nominal reservation',quantity=area([r])/(92903.04*COS),unit='sf',status='reservation')
joint=(W//2-100,glazed[1],W//2+100,glazed[3]);wedge('Opaque/PC raised flashing reservation',joint,lambda y:roof_base+P*y,lambda y:roof_base+25+P*y,finish,10,'Hybrid roof joint flashing reservation',quantity=(glazed[3]-glazed[1])/(304.8*COS),unit='lf',status='reservation')
for i in range(math.ceil((glazed[2]-glazed[0])/(18*IN))):
    x=glazed[0]+i*18*IN;r=(x,glazed[1],min(x+p['exterior_depth_mm'],glazed[2]),glazed[3]);wedge('Exterior shade slat '+str(i),r,lambda y:roof_base+305+P*y,lambda y:roof_base+305+p['stud_mm']+P*y,wood,11,'Exterior shading reservation',quantity=(glazed[3]-glazed[1])/(304.8*COS),unit='lf',status='reservation')
for i,x in enumerate([W//2+mm(5),W//2+mm(17),W//2+mm(29),W//2+mm(41)]):
    r=(x,D-mm(4),x+mm(4),D-mm(2));wedge('Vent reservation '+str(i),r,lambda y:roof_base+20+P*y,lambda y:roof_base+220+P*y,finish,11,'High-level roof vent reservation',quantity=1,unit='each',status='reservation')
# Interior dry partitions: exact US 2x4 profile, resolved union, holes propagated to skins.
part_region=sub(rect_union([wallband(e) for e in internal],clip=fp),all_ext)
def coreband(e,lo=None,hi=None):
    lo=e['lo'] if lo is None else lo;hi=e['hi'] if hi is None else hi;a=e['at']-p['interior_depth_mm']/2;b=e['at']+p['interior_depth_mm']/2
    return (lo,a,hi,b) if e['axis']=='x' else (a,lo,b,hi)
core=sub(rect_union([coreband(e) for e in internal],clip=fp),all_ext);skin=sub(part_region,core);walllayers(skin,plaster,12,'Partition lining',(114-p['interior_depth_mm'])/2)
# Top bands follow the sloping roof; conservative studs terminate at low roof datum.
for i,r in enumerate(sub(core,openingcuts(10))):box(f'2x4 sole plate {i}',r,0,p['stud_mm'],wood,12,'Partition timber 2x4')
for ply in [1,2]:
    for i,r in enumerate(core):wedge(f'2x4 sloped top plate {ply}-{i}',r,lambda y,k=ply:BASE+P*y-k*p['stud_mm']/COS,lambda y,k=ply:BASE+P*y-(k-1)*p['stud_mm']/COS,wood,12,'Partition timber 2x4')
studs=[]
for e in internal:
    for j in range(math.ceil((e['hi']-e['lo'])/p['stud_spacing_mm'])):
        along=e['lo']+j*p['stud_spacing_mm'];studs+=rect_union([coreband(e,along-p['stud_mm']/2,along+p['stud_mm']/2)],clip=core)
for z0,z1 in [(p['stud_mm'],2235),(2235,BASE-2*p['stud_mm'])]:
    for i,r in enumerate(sub(rect_union(studs),openingcuts((z0+z1)/2))):
        if z0==2235:wedge(f'2x4 upper stud {i}',r,lambda y:2235,lambda y:BASE+P*y-2*p['stud_mm']/COS,wood,12,'Partition timber 2x4')
        else:box(f'2x4 stud {z0}-{i}',r,z0,z1,wood,12,'Partition timber 2x4')
for i,e in enumerate(screen):
    for z0,z1 in [(0,152),(152,2743)]:
        for j,r in enumerate(sub([wallband(e)],openingcuts((z0+z1)/2))):box(f'Humidity screen {i}-{j}-{z0}',r,z0,z1,glass,12,'Glazed garden separation reservation',quantity=area([r])/152*(z1-z0)/92903.04,unit='sf',status='reservation')
    wedge('Humidity screen upper '+str(i),wallband(e),lambda y:2743,lambda y:BASE+P*y,glass,12,'Glazed garden separation reservation',quantity=(e['hi']-e['lo'])*(BASE+P*(e['lo']+e['hi'])/2-2743)/92903.04,unit='sf',status='reservation')
for o in m['openings']:
    e=emap[o['host']]
    if o['kind'] in ['window','sliding']:
        r=wallband(e,o['lo'],o['hi']);box(o['id']+' glazing reservation',r,o['sill'],o['head'],glass,12,'Window / sliding unit reservation',quantity=1,unit='each',status='reservation',host=o['id'])
    elif o['kind']=='door':
        sign=1 if e['positive']==o['room'] else -1;face=e['at']+sign*(e['thickness'] if e in ext else e['thickness']/2);hinge=o['lo']+51
        r=(hinge-19,min(face,face+sign*914),hinge+19,max(face,face+sign*914));box(o['id']+' open leaf',r,0,2134,wood,12,'Door unit reservation',quantity=1,unit='each',status='reservation',host=o['id'])
for f in m['fixtures']:
    ma=wood if f['kind']=='planter' else furniture;part='Waterproofed planter reservation' if f['kind']=='planter' else 'Furniture / fixture context'
    box(f['id'],f['rect'],0,f['height'],ma,13,part,quantity=area([f['rect']])/92903.04 if f['kind']=='planter' else None,unit='sf',status='reservation' if f['kind']=='planter' else 'context',host=f['room'])
    if f['kind']=='planter':
        a,b,c,d=f['rect'];box(f['id']+' vegetation',(a+80,b+80,c-80,d-80),f['height'],f['height']+350,leaf,13,'Vegetation context',status='context')
box('Ground context',(-mm(12),-mm(16),W+mm(12),D+mm(16)),-1100,-950,earth,1,'Terrain context',status='context')
box('South daylight/escape court',(-mm(2),-mm(10),W+mm(2),-20),-100,-20,aggregate,1,'Court / grade route reservation',status='context')
wedge('North burial context',(-mm(10),D+200,W+mm(10),D+mm(10)),lambda y:-950,lambda y:mm(8)*(D+mm(10)-y)/(mm(10)-200),earth,14,'Terrain context',status='context')
for label,r in [('West',(-mm(10),200,-200,D+200)),('East',(W+200,200,W+mm(10),D+200))]:wedge(label+' burial context',r,lambda y:-950,lambda y:mm(8)*max(0,y)/D,earth,14,'Terrain context',status='context')
for stage,name in STAGES.items():s.timeline_markers.new(f'{stage:02d} {name}',frame=(stage-1)*10+1)
s.frame_start=1;s.frame_end=151;s.frame_set(151);s.timeline_markers.new('COMPLETE',frame=151)
s.render.engine='CYCLES';s.cycles.samples=24;s.render.resolution_x=1800;s.render.resolution_y=950;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('Desert sky');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.78,.84,.9,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.8
bpy.ops.object.light_add(type='SUN');bpy.context.object.rotation_euler=(.45,-.25,-.45);bpy.context.object.data.energy=3
def camera(name,pos,target,scale):
    data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);s.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=scale;return ob
target=(W/2000,D/2000,1);cam=camera('Exterior',(42,-27,25),target,43);cutcam=camera('Cutaway',(39,-24,30),target,39);topcam=camera('Top',(W/2000,D/2000,40),(W/2000,D/2000,0),35);s.camera=cam
def scene(name,cam,exclude):
    a=s.copy();a.name=name;a.use_fake_user=True;a.camera=cam;a.frame_set(151)
    for c in a.view_layers[0].layer_collection.children:
        if any(c.name.startswith(f'{i:02d} ') for i in exclude):c.exclude=True
    return a
cut=scene('02 Owner furnished cutaway',cutcam,[7,8,9,10,11,14]);top=scene('03 Owner floor plan',topcam,[7,8,9,10,11,14]);structure=scene('04 Owner full-span structure',cam,[5,6,9,10,11,12,13,14])
for a in bpy.data.scenes:
    a.unit_settings.system='IMPERIAL';a.unit_settings.length_unit='FEET';a['source_sha256']=m['source_sha256'];a['brief_sha256']=m['brief_sha256'];a['source_svg']=m['source_path'];a['framing_profile_json']=json.dumps(p);a['status']='Three-zone / gross area / 50-50 roof confirmed; C1 dimensions and roof products remain provisional for engineer optimization'
bpy.context.window.scene=s;s.frame_set(151);(RUN/'model').mkdir(parents=True,exist_ok=True);(RUN/'review').mkdir(exist_ok=True)
native=RUN/'model/Owner-Earthship.blend';bpy.ops.wm.save_as_mainfile(filepath=str(native))
receipt=dict(source_svg=m['source_path'],source_sha256=m['source_sha256'],brief_sha256=m['brief_sha256'],native_file=str(native.relative_to(ROOT)),framing_profile=p,original_components=len(components),stages=STAGES,beam_count=len(beam_x),beam_actual_section_in=[m['beam_width_in'],m['beam_depth_in']],beam_gross_span_ft=D/304.8,beam_clear_span_ft=(D-914)/304.8,roof_pitch=P,roof_type='50% opaque / 50% polycarbonate; no soil on roof',status='Unengineered concept, not approved/stamped; glazing lengths and moisture/thermal details unresolved')
(RUN/'model/assembly-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
for a,name in [(s,'exterior'),(cut,'cutaway'),(top,'floor-plan'),(structure,'structure')]:a.render.filepath=str(RUN/'review'/f'{name}.png');bpy.ops.render.render(write_still=True,scene=a.name)
print('OWNER MODEL SAVED',len(components),'components')
