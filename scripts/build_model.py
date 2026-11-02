"""Background Blender authoring from actual semantic SVG; run with --python.
Own recipe for this single-story study, not the skill's gated family-wing recipe.
"""
import sys, math, json, csv, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from design import read_svg, validate, rect_union, sub, band, mm, area
import bpy
from mathutils import Vector

SOURCE=ROOT/'plans'/'A-long-ranch.svg'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if '--scheme' in args:SOURCE=ROOT/'plans'/(args[args.index('--scheme')+1]+'.svg')
M=read_svg(SOURCE);validate(M)
W,H=M['width'],M['depth'];HEIGHT=2743;PITCH=1/48
# Plan datums stay integer mm; construction stock dimensions are defined in inches.
IN=25.4
TWO_BY=1.5*IN;STUD_DEPTH=3.5*IN;HEADER_DEPTH=5.5*IN;SPACING=16*IN
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.name='01 Construction sequence';scene.unit_settings.system='IMPERIAL';scene.unit_settings.length_unit='FEET';scene.unit_settings.scale_length=1
scene['source_svg']=str(SOURCE.relative_to(ROOT));scene['source_sha256']=M['source_sha256'];scene['status']='Layout A selected by user; conceptual assemblies require engineering'
collections={};materials={};components=[]
STAGES={1:'Excavation and prepared subgrade',2:'Footings',3:'Capillary break and slab',4:'Retaining shell',5:'Waterproofing and exterior insulation',6:'Drainage',7:'Interior framing',8:'Wall finishes',9:'Engineered roof reservations',10:'Roof deck and insulation',11:'Roof membrane and overhang',12:'Windows and doors',13:'Fixtures and furnishings',14:'Earth berm context'}
def mat(name,color):
    if name not in materials:
        m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.7;materials[name]=m
    return materials[name]
def coll(stage):
    if stage not in collections:
        c=bpy.data.collections.new(f'{stage:02d} {STAGES[stage]}');scene.collection.children.link(c);collections[stage]=c
    return collections[stage]
def mesh(name,verts,faces,material,stage,part,host='',quantity=None,unit='ft3',measured=True):
    me=bpy.data.meshes.new(name);me.from_pydata([(x/1000,y/1000,z/1000) for x,y,z in verts],[],faces);me.update()
    o=bpy.data.objects.new(name,me);coll(stage).objects.link(o);o.data.materials.append(material)
    o['component_id']=f'C{len(components)+1:05}';o['part']=part;o['stage']=stage;o['level']='single-story';o['host']=host;o['assembly']=part;o['source_sha256']=M['source_sha256'];o['measured']=measured;o['quantity_unit']=unit
    if quantity is not None:o['quantity']=quantity
    components.append(o)
    start=(stage-1)*10+1
    for frame,hidden in [(1,stage!=1),(max(1,start-1),True),(start,False),(151,False)]:
        o.hide_render=hidden;o.hide_viewport=hidden;o.keyframe_insert('hide_render',frame=frame);o.keyframe_insert('hide_viewport',frame=frame)
    if o.animation_data and o.animation_data.action:
        try:
            for fc in o.animation_data.action.fcurves:
                for k in fc.keyframe_points:k.interpolation='CONSTANT'
        except AttributeError:pass
    return o
FACES=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def prism(name,r,z0,z1,material,stage,part,host='',**kw):
    a,b,c,d=r;verts=[(a,b,z0),(c,b,z0),(c,d,z0),(a,d,z0),(a,b,z1),(c,b,z1),(c,d,z1),(a,d,z1)]
    return mesh(name,verts,FACES,material,stage,part,host,**kw)
def wedge(name,r,low,high,material,stage,part,**kw):
    a,b,c,d=r;vs=[(a,b,low(b)),(c,b,low(b)),(c,d,low(d)),(a,d,low(d)),(a,b,high(b)),(c,b,high(b)),(c,d,high(d)),(a,d,high(d))]
    return mesh(name,vs,FACES,material,stage,part,**kw)
concrete=mat('Concrete',(0.58,.59,.55));wood=mat('Timber',(.58,.36,.16));finish=mat('Mineral plaster',(.87,.82,.7));insulation=mat('Rigid insulation',(.61,.73,.69));black=mat('Waterproofing',(.065,.09,.09));gravel=mat('Washed aggregate',(.4,.43,.4));soil=mat('Earth berm context',(.38,.3,.18));roofmat=mat('Light roof finish',(.58,.65,.62));glass=mat('Glazing reservation',(.25,.53,.58));furn=mat('Furniture',(.64,.45,.28));ceramic=mat('Fixtures',(.88,.9,.86))
fp=[(0,0,W,H)];ed=M['edges'];emap={e['id']:e for e in ed};ext=[e for e in ed if None in (e['negative'],e['positive'])];internal=[e for e in ed if e not in ext and e['id'] not in M['virtual']]
outside=rect_union([band(e) for e in ext],clip=fp)
def cuts(z):return [band({**emap[o['host']],'lo':o['lo'],'hi':o['hi']}) for o in M['openings'] if o['sill']<=z<o['head']]
levels=sorted({0,HEIGHT}|{o[k] for o in M['openings'] for k in ['sill','head']})
def wallsolids(domain,material,stage,part):
    for z0,z1 in zip(levels,levels[1:]):
        for i,r in enumerate(sub(domain,cuts((z0+z1)/2))):prism(f'{part} {z0} {i}',r,z0,z1,material,stage,part)
# Footing ring, no overlaps at corners; 24 x 12 in declared geometry only.
foot=rect_union([(-mm(.5),-mm(.5),W+mm(.5),mm(1.5)),(-mm(.5),H-mm(1.5),W+mm(.5),H+mm(.5)),(-mm(.5),mm(1.5),mm(1.5),H-mm(1.5)),(W-mm(1.5),mm(1.5),W+mm(.5),H-mm(1.5))])
# Interior bearing line at gallery's north edge; pads/header span need engineering.
hy=max(M['spaces']['Gallery'][1],M['spaces']['Gallery'][3]);foot=rect_union(foot+[(mm(1.5),hy-mm(1),W-mm(1.5),hy+mm(1))])
for i,r in enumerate(foot):prism('Footing '+str(i),r,-610,-305,concrete,2,'Concrete footings')
slab=(305,305,W-305,H-305)
prism('Compacted aggregate',slab,-305,-153,gravel,3,'Subslab aggregate')
prism('Subslab insulation',slab,-153,-103,insulation,3,'Subslab insulation',quantity=area([slab])/92903.04,unit='sf')
prism('Vapor barrier',slab,-103,-102,black,3,'Slab vapor barrier',quantity=area([slab])/92903.04,unit='sf')
prism('Four inch slab',slab,-102,0,concrete,3,'Concrete slab')
# Total 305 mm external assembly: 7 drain / 3 membrane / 76 insulation / 203 core / 16 finish.
previous=[]
for depth,material,stage,part in [(7,gravel,6,'Wall drainage layer'),(10,black,5,'Wall waterproofing'),(86,insulation,5,'Wall rigid insulation'),(289,concrete,4,'Retaining concrete core'),(305,finish,8,'Exterior wall inside finish')]:
    region=rect_union([band(e,depth) for e in ext],clip=fp);layer=sub(region,previous);wallsolids(layer,material,stage,part);previous=region
    # Close wedge above horizontal ceiling to sloping roof structure underside.
    for i,r in enumerate(layer):wedge(part+' upper closure '+str(i),r,lambda y:HEIGHT,lambda y:HEIGHT+406+y*PITCH,material,stage,part)
# Exact US dressed 2x4 partitions: 1.5 x 3.5 in, at 16 in on center.
pdomain=sub(rect_union([band(e) for e in internal],clip=fp),outside)
def framing_band(e,lo=None,hi=None,across0=None,across1=None):
    lo=e['lo'] if lo is None else lo;hi=e['hi'] if hi is None else hi
    a=e['at']-STUD_DEPTH/2 if across0 is None else across0
    b=e['at']+STUD_DEPTH/2 if across1 is None else across1
    return (lo,a,hi,b) if e['axis']=='x' else (a,lo,b,hi)
cores=sub(rect_union([framing_band(e) for e in internal],clip=fp),outside)
lining=sub(pdomain,cores);wallsolids(lining,finish,8,'Partition gypsum')
for z0,z1 in [(0,TWO_BY),(HEIGHT-2*TWO_BY,HEIGHT-TWO_BY),(HEIGHT-TWO_BY,HEIGHT)]:
    for i,r in enumerate(sub(cores,cuts(10) if z0==0 else [])):prism('Partition plate '+str(z0)+' '+str(i),r,z0,z1,wood,7,'Partition timber')
studs=[];headers=[];header_top=2134+HEADER_DEPTH
for e in internal:
    for along in [e['lo']+i*SPACING for i in range(math.ceil((e['hi']-e['lo'])/SPACING))]+[e['hi']-TWO_BY/2]:
        r=framing_band(e,along-TWO_BY/2,along+TWO_BY/2)
        studs.extend(rect_union([r],clip=cores))
    for o in M['openings']:
        if o['host']!=e['id']:continue
        for along in [o['lo']-1.5*TWO_BY,o['lo']-TWO_BY/2,o['hi']+TWO_BY/2,o['hi']+1.5*TWO_BY]:
            r=framing_band(e,along-TWO_BY/2,along+TWO_BY/2)
            studs.extend(rect_union([r],clip=cores))
        # Two dressed 2x6 plies and a 1/2-in plywood spacer; engineering reservation.
        lo,hi=o['lo']-TWO_BY,o['hi']+TWO_BY
        a=e['at']-STUD_DEPTH/2
        spans=[(a,a+TWO_BY,'Partition header 2x6'),(a+TWO_BY,a+STUD_DEPTH-TWO_BY,'Header plywood spacer'),(a+STUD_DEPTH-TWO_BY,a+STUD_DEPTH,'Partition header 2x6')]
        headers.append(framing_band(e,lo,hi))
        for p,(u,v,part) in enumerate(spans):
            for i,rr in enumerate(rect_union([framing_band(e,lo,hi,u,v)],clip=cores)):
                prism('Door header '+o['id']+f' ply {p}-{i}',rr,2134,header_top,wood,7,part,o['id'])
studs=rect_union(studs)
for z0,z1 in [(TWO_BY,2134),(2134,header_top),(header_top,HEIGHT-2*TWO_BY)]:
    region=sub(studs,cuts((z0+z1)/2))
    if z0==2134:region=sub(region,headers)
    for i,r in enumerate(region):prism('Partition stud '+str(z0)+' '+str(i),r,z0,z1,wood,7,'Partition timber')
# Sloped engineered roof assemblies are explicit reservations, not stock 2x lumber.
# A bearing/transfer line aligns with the gallery north edge.
for x in range(350,W-350,610):
    for j,(y0,y1) in enumerate([(305,hy),(hy,H-305)]):
        r=(x-45,y0,x+45,y1)
        wedge(f'Engineered roof member {x} {j}',r,lambda y:HEIGHT+y*PITCH,lambda y:HEIGHT+406+y*PITCH,wood,9,'Engineered roof member reservation',quantity=(y1-y0)/304.8*math.sqrt(1+PITCH**2),unit='lf',measured=False)
prism('Transfer beam over public gallery', (305,hy-90,mm(24),hy+90),HEIGHT-356,HEIGHT,wood,9,'Transfer beam reservation',quantity=(mm(24)-305)/304.8,unit='lf',measured=False)
# Supporting posts at ends of public span; placed within exterior and service-wall ownership.
for x in [215,mm(24)]:prism('Transfer support reservation '+str(x),(x-90,hy-90,x+90,hy+90),0,HEIGHT-356,wood,9,'Transfer support reservation',quantity=1,unit='each',measured=False)
roofr=(-305,-914,W+305,H+305);roofarea=area([roofr])/92903.04*math.sqrt(1+PITCH**2)
for z0,z1,ma,st,part in [(HEIGHT+406,HEIGHT+424,wood,10,'Roof deck'),(HEIGHT+424,HEIGHT+576,insulation,10,'Roof continuous insulation'),(HEIGHT+576,HEIGHT+582,black,11,'Roof membrane'),(HEIGHT+582,HEIGHT+588,roofmat,11,'Roof protective finish')]:
    wedge(part,roofr,lambda y,z=z0:z+y*PITCH,lambda y,z=z1:z+y*PITCH,ma,st,part,quantity=roofarea,unit='sf')
prism('Flat ceiling',(305,305,W-305,H-305),HEIGHT-13,HEIGHT,finish,8,'Ceiling gypsum',quantity=area([(305,305,W-305,H-305)])/92903.04,unit='sf')
# Window and door placeholders remain separate and visibly schematic.
for o in M['openings']:
    e=emap[o['host']]
    if o['kind']=='window':
        r=band({**e,'lo':o['lo'],'hi':o['hi']},150)
        if e['axis']=='x':r=(r[0],e['at']+145,r[2],e['at']+165)
        prism('Window reservation '+o['id'],r,o['sill'],o['head'],glass,12,'Window reservation',o['id'],quantity=1,unit='each',measured=False)
    else:
        # Leaves shown fully open; clear doorway stays visible.
        sign=1 if e['positive']==o['room'] else -1;t=305 if e in ext else 57;face=e['at']+sign*t;lo=o['lo'];width=o['hi']-lo
        if e['axis']=='x':r=(lo-18,min(face,face+sign*width),lo+18,max(face,face+sign*width))
        else:r=(min(face,face+sign*width),lo-18,max(face,face+sign*width),lo+18)
        prism('Open door '+o['id'],r,0,o['head'],wood,12,'Door reservation',o['id'],quantity=1,unit='each',measured=False)
for f in M['fixtures']:prism(f['id'],f['rect'],0,f['height'],furn if f['kind'] in ['bed','sofa','wardrobe','table','cabinet'] else ceramic,13,'Furniture / fixture context',f['room'],measured=False)
# Footing drain centerline, shown as a square conduit reservation, separately counted in lf.
for i,(r,length) in enumerate([((-203,-203,W+203,-101),(W+406)/304.8),((-203,H+101,W+203,H+203),(W+406)/304.8),((-203,-101,-101,H+101),(H+202)/304.8),((W+101,-101,W+203,H+101),(H+202)/304.8)]):
    prism('Perimeter drain route '+str(i),r,-480,-378,black,6,'Footing drain reservation',quantity=length,unit='lf',measured=False)
# Terrain is illustrative and does not enter purchased quantities.
berm_top=1829;toe=5486
wedge('North berm',( -toe,H+203,W+toe,H+toe),lambda y:-610,lambda y:berm_top*(H+toe-y)/(toe-203),soil,14,'Terrain context',measured=False)
# Side berms taper toward the exposed south face; wedges taper with northing.
for label,r in [('West',(-toe,305,-203,H+203)),('East',(W+203,305,W+toe,H+203))]:
    wedge(label+' berm',r,lambda y:-610,lambda y:max(0,berm_top*(y-305)/H),soil,14,'Terrain context',measured=False)
prism('Ground context',(-mm(24),-mm(24),W+mm(24),H+mm(24)),-800,-650,soil,1,'Terrain context',measured=False)
prism('South terrace',(-mm(2),-mm(10),W+mm(2),-50),-152,-50,concrete,14,'Patio allowance',quantity=(W+mm(4))*mm(10)/92903.04,unit='sf',measured=False)
for stage,name in STAGES.items():scene.timeline_markers.new(f'{stage:02d} {name}',frame=(stage-1)*10+1)
scene.timeline_markers.new('COMPLETE',frame=151);scene.frame_start=1;scene.frame_end=151;scene.frame_set(151)
# Scene setup, ambient light and cameras. Render only native authored geometry.
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Desert daylight');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.72,.8,.88,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
bpy.ops.object.light_add(type='SUN',location=(0,0,20));sun=bpy.context.object;sun.name='Sun';sun.rotation_euler=(math.radians(25),math.radians(-20),math.radians(-25));sun.data.energy=3
def camera(name,pos,target,scale):
    data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=scale;return ob
cam=camera('Exterior south-west',(29,-25,22),(W/2000,H/2000,0),34);scene.camera=cam
cutcam=camera('Furnished cutaway',(27,-21,27),(W/2000,H/2000,0),29)
topcam=camera('Plan camera',(W/2000,H/2000,35),(W/2000,H/2000,0),24)
# Consistent collection visibility through per-scene layer exclusions.
def make_scene(name,camera,excluded):
    s=scene.copy();s.name=name;s.use_fake_user=True;s.camera=camera;s.frame_set(151)
    for lc in s.view_layers[0].layer_collection.children:
        if any(lc.name.startswith(f'{i:02d} ') for i in excluded):lc.exclude=True
    return s
cut=make_scene('02 Furnished cutaway',cutcam,[9,10,11,14]);top=make_scene('03 Floor plan',topcam,[9,10,11,14]);structure=make_scene('04 Structure',cam,[5,6,8,10,11,12,13,14])
# Exclude ceiling only from cutaway/plan via linked visibility? Ceiling has own collection.
ceiling=bpy.data.objects.get('Flat ceiling');old=ceiling.users_collection[0];old.objects.unlink(ceiling);cc=bpy.data.collections.new('08 Ceiling only');scene.collection.children.link(cc);cc.objects.link(ceiling)
for s in [cut,top]:
    if cc.name not in s.collection.children:s.collection.children.link(cc)
    s.view_layers[0].layer_collection.children[cc.name].exclude=True
for s in [structure]:
    if cc.name not in s.collection.children:s.collection.children.link(cc)
    s.view_layers[0].layer_collection.children[cc.name].exclude=True
bpy.context.window.scene=scene
scene.frame_set(151)
for s in bpy.data.scenes:
    s['source_sha256']=M['source_sha256'];s.unit_settings.system='IMPERIAL';s.unit_settings.length_unit='FEET'
out=ROOT/'model'/'Earth-Groundship.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
receipt=dict(source_svg=str(SOURCE.relative_to(ROOT)),source_sha256=M['source_sha256'],native_file=str(out.relative_to(ROOT)),component_count=len(components),stages=STAGES,structural_status='Schematic only; roof members, transfer system, reinforcement, bearing and footing sizing require engineering',terrain_status='Illustrative massing, not a grading/excavation takeoff')
receipt['stock_dimensions_in']={'nominal_2x4_actual':[1.5,3.5],'nominal_2x6_actual':[1.5,5.5],'header_spacer':0.5,'stud_spacing':16}
(ROOT/'model'/'assembly-receipt.json').write_text(json.dumps(receipt,indent=2))
for s,filename in [(scene,'exterior.png'),(cut,'cutaway.png'),(top,'floor-plan.png'),(structure,'structure.png')]:
    s.render.filepath=str(ROOT/'review'/filename);bpy.ops.render.render(write_still=True,scene=s.name)
print('SAVED',out,'COMPONENTS',len(components))
