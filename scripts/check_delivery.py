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
assert all(x['purchase_unit'] in ['board-equivalent','sheet','cy','board','roll','lot','stick','lf','sf','each'] for x in e['material_rows'])
assert r['stock_dimensions_in']['nominal_2x4_actual']==[1.5,3.5]
assert r['stock_dimensions_in']['nominal_2x6_actual']==[1.5,5.5]
assert r['stock_dimensions_in']['stud_spacing']==16
with (ROOT/'materials/components.csv').open(newline='') as f:
    reader=csv.DictReader(f);assert 'volume_cf' in reader.fieldnames and 'volume_m3' not in reader.fieldnames
assert '38×89' not in (ROOT/'README.md').read_text(encoding='utf-8')
result=dict(local_links_checked=len(checked),budget_arithmetic='pass',stock_dimensions='pass',US_purchasing_units='pass',source_native_cost_provenance='pass',native_sha256=nativehash,source_sha256=svghash)
(ROOT/'review/delivery-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
