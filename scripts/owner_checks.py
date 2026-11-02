"""Delivery, provenance, area/roof, gate and cost checks for the owner revision."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,hashlib,tempfile,xml.etree.ElementTree as E
from owner_plan import ROOT,RUN,BRIEF_HASH,read_owner,validate,NS

class Links(HTMLParser):
    def __init__(self):super().__init__();self.urls=[]
    def handle_starttag(self,tag,attrs):self.urls += [v for k,v in attrs if k in ['href','src','data'] and v]
def main():
    plan=RUN/'plans/C1-owner-linear-100x25.svg';m=read_owner(plan);v=validate(m);validate(read_owner(RUN/'plans/C2-owner-linear-83x30.svg'))
    assert abs(v['gross_enclosed_sf']-2500)<.01 and m['width']==30480 and m['depth']==7620
    native=RUN/'model/Owner-Earthship.blend';nh=hashlib.sha256(native.read_bytes()).hexdigest();n=json.loads((RUN/'model/native-readback.json').read_text(encoding='utf-8'));e=json.loads((RUN/'materials/estimate.json').read_text(encoding='utf-8'));q=json.loads((RUN/'materials/quantities.json').read_text(encoding='utf-8'));p=json.loads((RUN/'project/project-plan.json').read_text(encoding='utf-8'))
    assert n['native_sha256']==e['native_sha256']==q['native_sha256']==nh
    assert n['source_sha256']==e['source_sha256']==q['source_sha256']==m['source_sha256']
    assert n['brief_sha256']==e['brief_sha256']==q['brief_sha256']==p['brief_sha256']==BRIEF_HASH
    assert len(p['hold_points'])==9 and all('UNVERIFIED' in g['status'] and not g['evidence_file'] for g in p['hold_points'])
    assert all(r['status']=='NOT REQUESTED' for r in p['procurement'])
    assert e['overall_project_weeks']==[1,72] and e['construction_phase_envelope_weeks']==[22,72]
    for side in ['low','high']:
        assert abs(sum(r[side+'_usd'] for r in e['material_rows'])-e['material_'+side+'_usd'])<.011
        assert sum(r['person_hours_'+side]*r['billable_usd_per_worker_hour_'+side] for r in e['labor_rows'])==e['labor_'+side+'_usd']
        assert abs(e['material_'+side+'_usd']+e['labor_'+side+'_usd']+e['equipment_'+side+'_usd']-e['construction_'+side+'_usd'])<.011
    assert e['separate_rows'][0]['low_usd']==e['separate_rows'][0]['high_usd']==0
    urls=set()
    for path in [ROOT/'index.html',RUN/'materials/costs.html',RUN/'project/index.html',ROOT/'materials/costs.html',ROOT/'review/index.html']:
        parser=Links();markup=path.read_text(encoding='utf-8');parser.feed(markup)
        assert 'Esq.' not in markup,'Personal title leaked into public digest'
        for link in parser.urls:
            u=urlsplit(link)
            if u.scheme or u.netloc or not u.path:continue
            target=(path.parent/unquote(u.path)).resolve();assert target.is_relative_to(ROOT) and target.is_file(),(path,link);urls.add(str(target.relative_to(ROOT)))
    rejects=[]
    with tempfile.TemporaryDirectory(dir=ROOT/'.local') as td:
        for case in ['stale-wall','unsupported-transform','roof-split-change']:
            root=E.parse(plan).getroot()
            if case=='stale-wall':
                a=root.find(f'.//{{{NS}}}g[@id="wall-cells"]')[0];a.set('width',str(int(a.get('width'))+1))
            elif case=='unsupported-transform':root.find(f'.//{{{NS}}}g[@id="owner-geometry"]').set('transform','translate(1 0) scale(1 -1)')
            else:
                a=root.find(f'.//{{{NS}}}g[@id="roof-source"]')[0];a.set('width',str(int(a.get('width'))+1))
            temp=Path(td)/(case+'.svg');E.ElementTree(root).write(temp)
            try:read_owner(temp)
            except AssertionError:rejects.append(case)
            else:raise AssertionError('Failed to reject '+case)
    result=dict(source_sha256=m['source_sha256'],native_sha256=nh,brief_sha256=BRIEF_HASH,geometry_and_routes='pass',room_fixture_and_door_checks='pass',roof_halves='50/50 pass',original_components=n['original_components'],hold_points='9 unverified, no fabricated releases',budget_arithmetic='pass',PDF_phase_envelope='weeks 1-72 plus closeout',local_links_checked=len(urls),personal_source_identity='omitted from public HTML',negative_source_cases=rejects)
    (RUN/'review/delivery-checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
