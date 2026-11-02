"""Publication checks for linked local files, budget arithmetic and provenance."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,hashlib,csv
ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ['href','src','data'] and v:self.links.append(v)
checked=[]
for path in [ROOT/'index.html',ROOT/'materials/costs.html',ROOT/'review/index.html']:
    p=Links();p.feed(path.read_text(encoding='utf-8'))
    for link in p.links:
        u=urlsplit(link)
        if u.scheme or u.netloc or not u.path:continue
        target=(path.parent/unquote(u.path)).resolve()
        assert target.is_relative_to(ROOT) and target.is_file(),(path.name,link)
        assert 'edge-profile' not in str(target)
        checked.append(str(target.relative_to(ROOT)))
e=json.loads((ROOT/'materials/estimate.json').read_text());n=json.loads((ROOT/'model/native-readback.json').read_text());r=json.loads((ROOT/'model/assembly-receipt.json').read_text());q=json.loads((ROOT/'materials/quantities.json').read_text())
nativehash=hashlib.sha256((ROOT/'model/Earth-Groundship.blend').read_bytes()).hexdigest();svghash=hashlib.sha256((ROOT/'plans/A-long-ranch.svg').read_bytes()).hexdigest()
assert e['native_sha256']==n['native_sha256']==q['native_sha256']==nativehash
assert e['source_sha256']==n['source_sha256']==q['source_sha256']==svghash==r['source_sha256']
for key,rows in [('material',e['material_rows']),('overall',e['overall_rows'])]:
    for side in ['low','high']:assert abs(round(sum(x[side+'_usd'] for x in rows),2)-e[f'{key}_{side}_usd'])<.011
assert e['material_low_usd']<=e['material_high_usd']<e['overall_high_usd']
assert len(e['overall_rows'])==3,'Direct house scope must contain materials, labor and equipment only'
assert 'already acquired' in e['scope']
assert not any(r['category']=='Site materials' for r in e['material_rows']),'Optional patio entered house material subtotal'
assert e['separate_budget_items'][0]['low_usd']==e['separate_budget_items'][0]['high_usd']==0
labor=e['labor_rows'];ids={r['phase_id']:r for r in labor}
for side in ['low','high']:
    assert sum(r[f'person_hours_{side}'] for r in labor)==e[f'labor_person_hours_{side}']
    assert abs(sum(r[f'labor_{side}_usd'] for r in labor)-e[f'labor_{side}_usd'])<.011
    for row in labor:
        expected=row[f'person_hours_{side}']*row[f'billable_usd_per_person_hour_{side}']
        assert abs(expected-row[f'labor_{side}_usd'])<.011,'Crew size must not multiply person-hour labor twice'
        for dependency in filter(None,row['after'].split(';')):
            assert row[f'earliest_start_week_{side}']+.011>=ids[dependency][f'earliest_finish_week_{side}']
    for option in e['labor_options']:
        expected=e[f'material_{side}_usd']+option[f'labor_{side}_usd']+e[f'equipment_{side}_usd']+option[f'coordination_{side}_usd']
        assert abs(expected-option[f'total_{side}_usd'])<.011
assert e['labor_options'][1]['owner_hours_low']>0
assert e['labor_options'][1]['calendar_weeks_high']>=e['calendar_weeks_high']
assert all(x['purchase_unit'] in ['board-equivalent','sheet','cy','board','roll','lot','stick','lf','sf','each'] for x in e['material_rows'])
assert r['stock_dimensions_in']['nominal_2x4_actual']==[1.5,3.5]
assert r['stock_dimensions_in']['nominal_2x6_actual']==[1.5,5.5]
assert r['stock_dimensions_in']['stud_spacing']==16
with (ROOT/'materials/components.csv').open(newline='') as f:
    reader=csv.DictReader(f);assert 'volume_cf' in reader.fieldnames and 'volume_m3' not in reader.fieldnames
assert '38×89' not in (ROOT/'README.md').read_text(encoding='utf-8')
result=dict(local_links_checked=len(checked),budget_arithmetic='pass',construction_scope='pass',labor_hours_rates_and_dependencies='pass',stock_dimensions='pass',US_purchasing_units='pass',source_native_cost_provenance='pass',native_sha256=nativehash,source_sha256=svghash)
(ROOT/'review/delivery-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
