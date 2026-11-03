"""Fresh native readback; quantities from original V2 construction objects only."""
import sys,json,hashlib,csv,collections,math
from pathlib import Path
import bpy,bmesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from owner_plan import RUN,read_owner,validate
s=bpy.data.scenes['01 Owner construction sequence'];m=read_owner(ROOT/s['source_svg']);validate(m)
assert len(bpy.data.scenes)==4 and s['source_sha256']==m['source_sha256']
objects=[o for o in s.objects if 'component_id' in o];assert len({o['component_id'] for o in objects})==len(objects)
# Verify the user's clear roof revision in the saved native file.
assert not any(o['part']=='Exterior shading reservation' for o in objects)
panels=[o for o in objects if o['part']=='Polycarbonate 5/8 in nominal reservation']
assert len(panels)==13
for panel in panels:
    shader=panel.data.materials[0].node_tree.nodes.get('Principled BSDF')
    assert shader.inputs['Transmission Weight'].default_value==1
    assert shader.inputs['Roughness'].default_value<.03
rows=[];groups=collections.defaultdict(lambda:dict(net_quantity=0,component_count=0,statuses=set()))
for o in objects:
    assert all(abs(v-1)<1e-8 for v in o.scale) and all(math.isfinite(x) for v in o.data.vertices for x in v.co)
    bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_manifold for e in bm.edges),o.name;vol=abs(bm.calc_volume(signed=True));bm.free();assert vol>0,o.name
    if o['status']=='context':continue
    part=o['part'];unit=o['quantity_unit'];qty=o.get('quantity');basis='Native volume'
    if qty is None:
        if 'Concrete' in part or 'concrete' in part or part=='Subslab aggregate':qty=vol/.764554857984;unit='cy'
        elif 'thickness_in' in o:qty=vol/(o['thickness_in']*.0254)/.09290304;unit='sf';basis='Native volume / declared layer thickness'
        elif part=='Partition timber 2x4':qty=vol/(.0381*.0889)/.3048;unit='equivalent lf';basis='Native timber volume / dressed 1.5 x 3.5 in section'
        else:qty=vol/.028316846592;unit='cf'
    else:basis='Source assembly area/length/count reservation' if o['status']=='reservation' else 'Native source area/length'
    row=dict(component_id=o['component_id'],part=part,stage=o['stage'],quantity=round(qty,5),unit=unit,volume_cf=round(vol/.028316846592,7),status=o['status'],basis=basis);rows.append(row)
    g=groups[(part,unit)];g['net_quantity']+=qty;g['component_count']+=1;g['statuses'].add(o['status'])
for stage in range(1,15):
    s.frame_set((stage-1)*10+1)
    for o in objects:assert o.hide_render==o.hide_viewport==(o['stage']>stage),(stage,o.name)
s.frame_set(151)
beams=[o for o in objects if o['part']=='Glulam beam reservation'];assert len(beams)==14
for b in beams:
    assert abs((max(v.co.x for v in b.data.vertices)-min(v.co.x for v in b.data.vertices))/.0254-5.125)<.001
    assert abs((b.data.vertices[4].co-b.data.vertices[0].co).length/.0254-18)<.001
    assert b['span_axis']=='north-south'
assert all(abs(a-b)<1e-8 for a,b in zip(json.loads(s['framing_profile_json'])['actual_wall_stock_in']['interior'],[1.5,3.5]))
assert not any('Transfer beam' in o.name or 'Transfer support' in o.name for o in objects)
for fixture in m['fixtures']:
    ob=bpy.data.objects.get(fixture['id']);assert ob is not None
    actual=[min(v.co.x for v in ob.data.vertices),min(v.co.y for v in ob.data.vertices),max(v.co.x for v in ob.data.vertices),max(v.co.y for v in ob.data.vertices)]
    assert all(abs(a-b/1000)<.0001 for a,b in zip(actual,fixture['rect'])),('Saved fixture differs from source',fixture['id'])
native=RUN/'model/Owner-Earthship.blend';nh=hashlib.sha256(native.read_bytes()).hexdigest()
receipt=dict(source_sha256=m['source_sha256'],brief_sha256=m['brief_sha256'],native_sha256=nh,original_components=len(objects),scenes=4,closed_positive_volume_meshes='pass',all_14_reveal_stages='pass',finite_coordinates_and_unit_scale='pass',full_span_beams=14,beam_section_metrology='5.125 x 18 in, pass',framing_system='us',limits=['No engineering, reinforcement, universal clash, drainage or code approval.','Glulam/PC/frame/shade/vent/connection dimensions are reservations, not shop drawings.','Court-to-grade route and actual approval documents remain unresolved.'])
(RUN/'model/native-readback.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');(RUN/'materials').mkdir(exist_ok=True)
with (RUN/'materials/components.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
out=[]
for (part,unit),g in sorted(groups.items()):out.append(dict(item=part,net_quantity=round(g['net_quantity'],2),unit=unit,status='/'.join(sorted(g['statuses'])),component_count=g['component_count']))
with (RUN/'materials/bill-of-materials.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
(RUN/'materials/quantities.json').write_text(json.dumps(dict(source_sha256=m['source_sha256'],brief_sha256=m['brief_sha256'],native_sha256=nh,items=out),indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
if '--render-stages' in sys.argv:
    s.cycles.samples=8;s.render.resolution_x=1100;s.render.resolution_y=580;(RUN/'review/stages').mkdir(exist_ok=True)
    for stage in range(1,15):s.frame_set((stage-1)*10+1);s.render.filepath=str(RUN/'review/stages'/f'{stage:02}.png');bpy.ops.render.render(write_still=True,scene=s.name)
