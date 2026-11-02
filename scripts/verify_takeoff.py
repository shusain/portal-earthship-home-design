"""Fresh Blender-file readback and takeoff; never saves or modifies the model."""
import sys,json,csv,hashlib,math,collections
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from design import read_svg,validate
scene=bpy.data.scenes['01 Construction sequence'];source=ROOT/scene['source_svg'];m=read_svg(source);validate(m)
assert len(bpy.data.scenes)==4,'Missing saved review scenes'
assert scene['source_sha256']==m['source_sha256'],'Stale model source'
objects=[o for o in scene.objects if 'component_id' in o];ids=[o['component_id'] for o in objects];assert len(ids)==len(set(ids))
rows=[];group=collections.defaultdict(lambda:dict(quantity=0,objects=0,volume_m3=0))
surface_thickness={'Wall drainage layer':.007,'Wall waterproofing':.003,'Wall rigid insulation':.076,'Exterior wall inside finish':.016,'Partition gypsum':(0.114-0.0889)/2,'Header plywood spacer':.0127}
for o in objects:
    assert all(abs(v-1)<1e-8 for v in o.scale)
    assert all(math.isfinite(c) for v in o.data.vertices for c in v.co)
    bm=bmesh.new();bm.from_mesh(o.data)
    assert all(e.is_manifold for e in bm.edges),('Nonmanifold',o.name)
    vol=abs(bm.calc_volume(signed=True));bm.free();assert vol>0,('Zero volume',o.name)
    part=o['part'];measured=o['measured'];unit=o['quantity_unit'];q=o.get('quantity',None)
    basis='Measured native mesh volume'
    if q is None:
        if 'concrete' in part.lower():q=vol/0.764554857984;unit='cy'
        elif part in surface_thickness:q=vol/surface_thickness[part]/.09290304;unit='sf';basis=f'Native mesh volume / {surface_thickness[part]/.0254:.5g} in declared layer thickness'
        elif part=='Partition timber':q=vol/(.0381*.0889)/.3048;unit='equivalent lf';basis='Net modeled wood / exact 1.5 x 3.5 in dressed 2x4 section; resolved junction pieces are volume equivalents, not a cut list'
        elif part=='Partition header 2x6':q=vol/(.0381*.1397)/.3048;unit='lf';basis='Net modeled wood / exact 1.5 x 5.5 in dressed 2x6 section; schematic header sizing'
        elif part=='Subslab aggregate':q=vol/.764554857984;unit='cy'
        else:q=vol/0.028316846592;unit='cf'
    elif measured:basis='Source surface area recorded on native object'
    else:basis='Schematic reservation / context; not a measured purchasing quantity'
    row=dict(component_id=o['component_id'],part=part,stage=o['stage'],name=o.name,host=o['host'],volume_cf=round(vol/.028316846592,8),quantity=round(q,5),unit=unit,status='measured' if measured else 'reservation',basis=basis)
    rows.append(row)
    if part not in ['Terrain context','Furniture / fixture context']:
        g=group[(part,unit,'measured' if measured else 'reservation')];g['quantity']+=q;g['objects']+=1;g['volume_m3']+=vol;g['basis']=basis
# Stage visibility verified in actual source scene, not other presentation scenes.
for stage in range(1,15):
    scene.frame_set((stage-1)*10+1)
    for o in objects:
        assert o.hide_render==(o['stage']>stage),(stage,o.name,'render visibility')
        assert o.hide_viewport==(o['stage']>stage),(stage,o.name,'viewport visibility')
scene.frame_set(151)
native=ROOT/'model'/'Earth-Groundship.blend';native_hash=hashlib.sha256(native.read_bytes()).hexdigest()
receipt=dict(source_sha256=m['source_sha256'],native_sha256=native_hash,unique_original_components=len(objects),closed_positive_volume_meshes='pass',finite_geometry='pass',unit_scale='pass',all_14_reveal_stages='pass',scene_count=len(bpy.data.scenes),source_geometry_readback='pass',limits=['No structural load/span design or comprehensive pairwise clash certification.','Layer ownership follows source union geometry; terrain/furnishings excluded from construction takeoff.','Windows/doors use reservations; certified clear opening dimensions remain unverified.'])
(ROOT/'model'/'native-readback.json').write_text(json.dumps(receipt,indent=2))
with (ROOT/'materials'/'components.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
allowances={'Concrete footings':5,'Concrete slab':5,'Retaining concrete core':5,'Partition timber':15,'Partition gypsum':10,'Ceiling gypsum':10,'Roof deck':10,'Roof membrane':15,'Wall waterproofing':15,'Wall rigid insulation':10,'Roof continuous insulation':10,'Subslab insulation':10,'Slab vapor barrier':15,'Footing drain reservation':10}
bom=[]
for (part,unit,status),g in sorted(group.items()):
    waste=allowances.get(part,10 if status=='measured' else 0)
    bom.append(dict(item=part,net_quantity=round(g['quantity'],2),unit=unit,status=status,allowance_percent=waste,planning_quantity=round(g['quantity']*(1+waste/100),2),component_count=g['objects'],basis=g['basis']))
for part,unit,note in [('Reinforcing steel','lb','Engineer to specify bars, laps, cover, dowels and schedule'),('Earthwork excavation and backfill','cy','Requires surveyed ground and engineered slopes; illustrative terrain is excluded'),('Drain stone and filter fabric','cy / sf','Requires drain trench and soil filter design'),('Connectors, anchors and waterproof penetrations','lot','Requires structural and envelope details'),('Roof bearing headers / posts / hold-downs','lot','Reservations shown; engineering and connection schedule required'),('HVAC, ventilation, plumbing and electrical','lot','Service routing and equipment sizing not modeled'),('PV / storage / cistern / septic / well','lot','Optional/site-dependent systems not sized'),('Floor finish and cabinets','sf / lf','Furniture is context; finish and cabinetry schedule not developed')]:
    bom.append(dict(item=part,net_quantity='',unit=unit,status='TBD',allowance_percent='',planning_quantity='',component_count='',basis=note))
with (ROOT/'materials'/'bill-of-materials.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(bom[0]));w.writeheader();w.writerows(bom)
(ROOT/'materials'/'quantities.json').write_text(json.dumps(dict(source_sha256=m['source_sha256'],native_sha256=native_hash,items=bom),indent=2))
body=['# Preliminary material takeoff','',f'Source SVG SHA256: `{m["source_sha256"]}`',f'Native Blender SHA256: `{native_hash}`','','All purchasing quantities use US units: linear feet (lf), square feet (sf), cubic feet (cf), cubic yards (cy), pounds (lb), boards, sheets, rolls and each. See [US purchasing and costs](cost-breakdown.md) for stock sizes, supplier links and the overall estimate. Measured quantities are separate from schematic reservations and purchasing allowances; these are not order quantities.','','| Item | Net | Unit | Status | Allowance | Planning quantity |','|---|---:|---|---|---:|---:|']
for r in bom:body.append(f'| {r["item"]} | {r["net_quantity"]} | {r["unit"]} | {r["status"]} | {r["allowance_percent"]} | {r["planning_quantity"]} |')
body+=['','Concrete volumes include only the modeled shell/slab/footings. Reinforcement is TBD. Drain and waterproofing quantities do not include outlet runs, cleanouts, flashing/laps beyond the listed allowance, protection details or penetration boots. Wall layers extend across all exterior faces, including the exposed front; later face-specific detailing may reduce the below-grade systems. Partition timber is a volume equivalent, not a cut list. Roof member reservations are not purchasable stock; a truss/joist supplier must engineer and quote them.','', 'Labor, tax, freight, equipment, engineered design, survey, permits, land, utilities and unmodeled site systems are excluded. No installed-cost claim is made.']
(ROOT/'materials'/'README.md').write_text('\n'.join(body),encoding='utf-8')
print(json.dumps(receipt,indent=2))
