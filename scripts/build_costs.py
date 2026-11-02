"""US purchasing units and transparent dated estimate from the native takeoff."""
from pathlib import Path
import json,csv,math,html
ROOT=Path(__file__).resolve().parents[1]
rates=json.loads((ROOT/'materials/us-rate-scenario-2026-11-02.json').read_text());src=rates['sources']
take=json.loads((ROOT/'materials/quantities.json').read_text());items={r['item']:r for r in take['items']}
rows=[]
def net(part):return float(items[part]['net_quantity'])
def add(name,category,qty,unit,low,high,source='',evidence='Planning allowance',basis='',netq=None,waste=None):
    assert qty>=0 and 0<=low<=high
    rows.append(dict(item=name,category=category,net_quantity=netq,quantity=round(qty,4),purchase_unit=unit,allowance_percent=waste,unit_low_usd=low,unit_high_usd=high,low_usd=round(qty*low,2),high_usd=round(qty*high,2),evidence=evidence,source_title=src[source]['title'] if source else '',source_url=src[source]['url'] if source else '',basis=basis))
def observed(key):return src[key]['observed_price']
def boards(part,stock,stocklen,waste,key,low=None,high=None):
    q=net(part);count=math.ceil(q*(1+waste/100)/stocklen)
    add(stock,'Framing',count,'board-equivalent',low or observed(key),(high or (low or observed(key))*1.3),key,'Advertised benchmark + authored upper reserve',f'{q:.2f} net lf x {1+waste/100:.2f} / {stocklen} ft, rounded up. Volume-derived planning equivalent; not a member count, splice plan or cut list.',q,waste)
boards('Partition timber','Nominal 2x4 x 10 ft SPF #2 or engineer-approved grade; dressed 1.5 x 3.5 in',10,15,'2x4')
boards('Partition header 2x6','Nominal 2x6 x 8 ft header stock; dressed 1.5 x 5.5 in',8,15,'2x6')
q=net('Header plywood spacer');add('1/2 in x 4 ft x 8 ft plywood for header spacers','Framing',math.ceil(q*1.15/32),'sheet',30,50,'plywood',basis='1/2 in spacer; roof-sheathing listing is sourcing-family reference, not an observed 1/2 in price',netq=q,waste=15)
for p in ['Concrete footings','Concrete slab','Retaining concrete core']:
    q=net(p);add(p+' — ready mix, specified mix TBD','Concrete',math.ceil(q*1.05*4)/4,'cy',180,280,'concrete',basis='Measured native volume plus 5%, rounded to 1/4 cy. Excludes delivery, pump, placement, forms and steel.',netq=q,waste=5)
add('Reinforcing steel supply, ties, chairs and anchor dowels','Concrete',1,'lot',4000,9000,basis='Authored supply allowance only; bar sizes, pounds, spacing, laps and cover require an engineered schedule. No measured steel quantity exists.')
q=net('Subslab aggregate');add('Specified capillary-break aggregate','Concrete',math.ceil(q*1.1),'cy',50,90,'aggregate',basis='10% loose-volume allowance; compaction and gradation unverified; trucking separate',netq=q,waste=10)
for p,key,thickness in [('Subslab insulation','xps2','2 in'),('Wall rigid insulation','xps3','3 in')]:
    q=net(p);add(f'{thickness} XPS rigid insulation, 4 ft x 8 ft','Insulation',math.ceil(q*1.1/32),'board',observed(key),round(observed(key)*1.25,2),key,'Advertised benchmark + authored upper reserve','25 psi product benchmark; required bearing, termite/envelope approval and R-value remain design inputs',q,10)
q=net('Roof continuous insulation');add('Roof-approved new polyiso, 3 in x 4 ft x 8 ft, TWO layers (6 in total)','Insulation',2*math.ceil(q*1.1/32),'board',55,90,'roofiso',basis='Two layers counted separately; 10% cutting waste per layer. Final thermal/uplift/fire/fastener design TBD.',netq=2*q,waste=10)
q=net('Wall waterproofing');add('Self-adhered foundation waterproofing, nominal 200 sf roll','Waterproofing',math.ceil(q*1.15/200),'roll',observed('wallwater'),round(observed('wallwater')*1.3,2),'wallwater','Advertised benchmark + authored upper reserve','15% for seams/cutting; all exterior faces retained from current study; primer/detail products separate',q,15)
q=net('Wall drainage layer');add('Drainage/protection composite, 4 ft x 50 ft roll','Waterproofing',math.ceil(q*1.1/200),'roll',observed('drainmat'),round(observed('drainmat')*1.3,2),'drainmat','Advertised benchmark + authored upper reserve','10% seam/cutting reserve; attachment and termination details TBD',q,10)
q=net('Slab vapor barrier');add('15 mil underslab vapor barrier, 14 ft x 140 ft roll','Waterproofing',math.ceil(q*1.15/1960),'roll',observed('vapor'),round(observed('vapor')*1.2,2),'vapor','Advertised benchmark + authored upper reserve','15% laps/penetrations; two full rolls leave substantial surplus; smaller roll quote may reduce cost',q,15)
add('Compatible waterproofing primers, boots, tape, mastic and terminations','Waterproofing',1,'lot',1800,3500,'wallwater',basis='Additional materials allowance; no labor; compatible manufacturer-approved assembly required')
q=net('Footing drain reservation');add('Engineered 4 in nominal footing-drain pipe, 10 ft sticks','Drainage',math.ceil(q*1.1/10),'stick',25,55,'pipe',basis='10% plus round-up. Link is an observed $16.38 thin-wall price comparison only; budget uses higher authored rate pending approved pipe class/burial design. Not a recommendation to use D2729 at 6 ft burial.',netq=q,waste=10)
add('Drain stone, filter fabric, cleanouts, outlet and upslope interceptor materials','Drainage',1,'lot',2500,6000,'aggregate',basis='Provisional materials only. Outlet length and trench/soil design are not measured.')
q=net('Engineered roof member reservation');add('Engineered 16 in-depth roof joist system — supplier-designed','Framing',math.ceil(q*1.1),'lf',6,12,'joist',basis='Complete joist assembly priced once; 10% bearing/trim reserve. Native boxes are reservations, not joist sections or an approved series.',netq=q,waste=10)
add('Transfer beam, posts, rim/blocking, hangers and anchors package','Framing',1,'lot',4500,10000,'joist',basis='Engineered quote required; includes connectors; partition headers already counted separately')
q=net('Roof deck');add('23/32 in rated roof sheathing plywood, 4 ft x 8 ft','Roof',math.ceil(q*1.1/32),'sheet',observed('plywood'),60,'plywood','Supplier search-listing benchmark; full page blocked; verify price','10% waste; final span rating, edge support, fastening and panel layout TBD',q,10)
q=net('Roof membrane');add('60 mil roof membrane benchmark, 10 ft x 100 ft roll','Roof',4,'roll',observed('epdm'),1400,'epdm','Advertised benchmark + authored upper reserve','Four roughly 66 ft courses, allowing laps across the roughly 38 ft roof depth; four full rolls purchased. Area-only ceil(area/1000)=3 is NOT used. Offcuts retained; final roll/seam plan by roofer.',q,None)
add('Roof cover board, adhesives, flashing, fascia, gutters and downspouts','Roof',1,'lot',6500,12000,'roofiso',basis='Covers the native Roof protective finish reservation plus unmodeled roof accessories; do not add that native row again')
q=net('Partition gypsum');add('1/2 in drywall, 4 ft x 8 ft wall sheets','Finishes',math.ceil(q*1.1/32),'sheet',observed('drywall'),25,'drywall','Advertised benchmark + authored upper reserve','10% waste; moisture-rated/wet-area backers included by separate allowance',q,10)
q=net('Ceiling gypsum');add('5/8 in sag-resistant ceiling board, 4 ft x 8 ft','Finishes',math.ceil(q*1.1/32),'sheet',22,32,'drywall',basis='Authored 5/8 in ceiling-board rate; linked 1/2 in product is a supplier reference only. Native ceiling is a thickness reservation; do not infer fire rating.',netq=q,waste=10)
q=net('Exterior wall inside finish');add('Mineral plaster over concrete interior faces','Finishes',math.ceil(q*1.1),'sf',1.25,2.5,basis='Material-only authored allowance; final finish/bonding system and supplier quote TBD',netq=q,waste=10)
add('Drywall tape/compound, screws, corner bead, wet-area backers and paint','Finishes',1,'lot',3000,6000,basis='Materials only; installation labor in overall budget')
add('8 interior nominal 36 x 84 in door units and hardware','Openings',8,'each',240,500,basis='Source aperture reservation is 36 in, not a finished prehung rough opening. Increase rough openings during detailed framing coordination; not a ready-to-order size.')
add('2 exterior nominal 36 x 84 in insulated entry units','Openings',2,'each',750,1800,basis='Rough-opening/product and landing coordination required; materials only')
add('3 bedroom escape-window units, approximately 4 x 5 ft openings','Openings',3,'each',800,1700,basis='Supplier must certify operable net escape area and sill, not just frame dimensions. Exact product unselected.')
add('1 living window unit, approximately 6 x 6 ft opening','Openings',1,'each',1000,2200,basis='Product, structural header, safety glazing and daylight design TBD')
add('Electrical materials, service panel, alarms and lighting','Services',1,'lot',6500,11500,basis='House wiring, panel, protection and existing off-grid interface materials only. Existing PV/battery/generator equipment already acquired; no utility extension included.')
add('Plumbing materials, two baths, kitchen and laundry fixtures','Services',1,'lot',8500,15000,basis='House materials only. Septic and off-house water source are outside this construction headline; their existing status is unconfirmed.')
add('Heat pump, balanced ventilation, ducts and water heater equipment','Services',1,'lot',9000,16000,basis='Equipment/material allowance; load calculation and installer quote required')
add('Cabinets, counters, appliances and finish flooring materials','Finishes',1,'lot',18000,32000,basis='Provisional midrange selection allowance; source furniture placeholders are not counted')
add('South patio materials, approximately 680 sf','Site materials',680,'sf',4,8,basis='Patio is outside enclosed area; material package only; labor included in house/site labor allowance as coordinated')
from construction_budget import build_report
build_report(ROOT,rates,take,rows)
