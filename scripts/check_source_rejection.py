"""Negative checks: reject unsupported/stale edited SVG and blocked functional access."""
import copy,json,tempfile,xml.etree.ElementTree as E
from pathlib import Path
from design import ROOT,NS,read_svg,validate
src=ROOT/'plans'/'A-long-ranch.svg';passed=[]
with tempfile.TemporaryDirectory() as td:
    for case in ['stale-wall','unsupported-transform','unhosted-opening']:
        root=E.parse(src).getroot()
        if case=='stale-wall':
            g=root.find(f'.//{{{NS}}}g[@id="wall-cells"]');g[0].set('width',str(int(g[0].get('width'))+1))
        elif case=='unsupported-transform':root.find(f'.//{{{NS}}}g[@id="geometry"]').set('transform','translate(1 0) scale(1 -1)')
        else:
            g=root.find(f'.//{{{NS}}}g[@id="opening-source"]');r=next(e for e in g if e.tag=='{'+NS+'}rect');r.set('data-hi','999999')
        path=Path(td)/f'{case}.svg';E.ElementTree(root).write(path)
        try:read_svg(path)
        except (AssertionError,ValueError):passed.append(case)
        else:raise AssertionError(f'Failed to reject {case}')
m=read_svg(src);m['fixtures'][0]['rect']=[0,0,500,500]
try:validate(m)
except AssertionError:passed.append('fixture-wall-clash')
else:raise AssertionError('Failed to reject fixture clash')
receipt=dict(rejected_cases=passed,passed=True)
(ROOT/'plans'/'negative-checks.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
