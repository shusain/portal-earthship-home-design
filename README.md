# Portal Earthship — owner brief V2

[Live design overview](https://shusain.github.io/portal-earthship-home-design/) · [Project controls](revisions/owner-brief-v2/project/index.html) · [Construction and program costs](revisions/owner-brief-v2/materials/costs.html)

The land owner's nine-page project plan supersedes the prior ranch study. The user confirmed **2,500 sf gross enclosed including garden/walls**, **three zones in a line**, and **50% translucent roof extending over part of the middle zone**. The raw PDF remains local; public artifacts use an anonymous requirements digest and record its SHA256. No source personal identity, deed/APN, call script or private approval documents are published.

## Current concept

- C1: provisional **100 ft x 25 ft**, 2,500 sf gross / approximately **2,102.79 sf clear**. Engineer to optimize dimensions against glulam, panel, retaining and site costs. No optimum or parcel fit is claimed.
- Gross zones: living/sleeping 1,000 sf; kitchen/bath/service 700 sf; garden 800 sf. The prior three-bedroom requirement is superseded. Bath is enclosed beneath opaque roof; a glazed garden humidity screen is a coordination proposal.
- One short-direction glulam span, no interior roof bearing line. Fourteen 5-1/8 x 18 in modeled beam reservations, 28 ft buying-length reservation; **no section, grade, span or connection approval**.
- Split roof: half opaque, half polycarbonate, before frame/shade deductions. Garden plus 450 sf of middle zone under PC before overhangs. Approximate 16 mm (5/8 in) panel thickness; actual panel lengths, support grid, joints and thermal system need manufacturer/engineer design.
- Roof slope provisionally 10% (1.2 in/ft), replacing old 1/4 in/ft. Glulam and secondary framing are inspectable; roof frame, flashing, gaskets, vents and exterior shading remain unengineered reservations.
- Retained walls and exposed roof with south daylight/escape court. Approximately 8 ft rear burial is illustrative only. Floor datum, stable slopes, court-to-grade escape route and gravity drain outlet need actual parcel/topographic/soil data.
- US framing profile: nominal 2x4 actual 1.5 x 3.5 in, nominal 2x6 actual 1.5 x 5.5 in, nominal 2x8 actual 1.5 x 7.25 in. Stud grid 16 in; purlin grid 24 in. Room datums are integer mm; stock/grid geometry preserves exact inch conversions. Purchasing uses US units.

## Current artifacts

Everything in [revisions/owner-brief-v2](revisions/owner-brief-v2) is this revision:

- [C1 semantic SVG](revisions/owner-brief-v2/plans/C1-owner-linear-100x25.svg), [C2 comparison](revisions/owner-brief-v2/plans/C2-owner-linear-83x30.svg), and [room areas](revisions/owner-brief-v2/plans/C1-owner-linear-100x25-rooms.csv).
- [Native Blender model](revisions/owner-brief-v2/model/Owner-Earthship.blend), [four-view overview](revisions/owner-brief-v2/review/overview.jpg), [stage animation](revisions/owner-brief-v2/review/construction.gif), [native readback](revisions/owner-brief-v2/model/native-readback.json).
- [BOM](revisions/owner-brief-v2/materials/bill-of-materials.csv), [per-component quantities](revisions/owner-brief-v2/materials/components.csv), [US purchasing/costs](revisions/owner-brief-v2/materials/us-purchasing-and-costs.csv), [trade labor](revisions/owner-brief-v2/materials/trade-labor.csv), [estimate JSON](revisions/owner-brief-v2/materials/estimate.json).
- [Owner brief reconciliation](revisions/owner-brief-v2/project/brief-reconciliation.md), [requirements matrix](revisions/owner-brief-v2/project/requirements-matrix.csv), [hold points](revisions/owner-brief-v2/project/hold-points.csv), [procurement register](revisions/owner-brief-v2/project/procurement-register.csv), [phase cash tracker](revisions/owner-brief-v2/project/phase-cash-tracker.csv), [decision register](revisions/owner-brief-v2/project/decision-register.csv), [weekly report template](revisions/owner-brief-v2/project/weekly-status-template.md).

Four native scenes and 14 material reveal stages use the same original construction objects; presentation views are not extra consumption. The model is not an excavation, installation or physical construction simulation. Roof vent boxes indicate reservations, not functioning cut openings; thermal/humidity/airflow capacity is uncalculated. Furniture/terrain context is excluded from takeoff; planters and engineered systems are explicitly reservations.

## Owner control requirements

All **nine hold points remain unverified**. No approval, permit, insurance confirmation, stamped drawing, inspection release, bid, delivery promise, actual payment or commitment has been invented. APN/exact zoning and approval records are missing. Owner approves decisions and payments; PM/design professionals/trades execute. No DIY labor or free PM execution is assumed. No contacts, applications, orders, payments or field work have been performed.

The PDF's phase-5 backfill-before-roof sequence needs an explicit structural release: full backfill waits for stamped temporary restraint or the completed accepted permanent restraint/diaphragm. Waterproofing inspection is not a structural bracing release.

Current [County owner-builder guidance](https://www.cochise.az.gov/212/Owner-Builder-Amendment) says Option 2 has no Certificate of Occupancy and retains an administrative final site visit; codes and non-building approvals still apply. Do not infer eligibility from acreage alone. Recorded disclosure, permit path, well/water/septic and insurer acceptance need actual written evidence.

The PDF's **weeks 1-72 overall phase envelope plus subsequent closeout** replaces the previous 21-37 week construction-only scenario. Construction phases are approximately project weeks 22-72, but stamped sequencing, approvals, quotes and written supply dates govern. No calendar start or final delivery date is known.

## Cost scope

The current report prices the new geometry, glulam, hybrid roof, exterior shading, vents, garden humidity system and waterproof planters. Construction materials/trade labor/equipment are separate from required architect/structural/soil/private inspection/delegated PM allowances. Freight/tax and an unapproved 20% contingency example are separate. Owner brief requires a contingency proposal after bids and owner approval; no percentage is approved.

Land and off-grid generation/storage are already acquired. House electrical/interface work remains. Short approved water/septic connection reserves are provisional; new wells/septic fields or long service runs are not priced. All new engineered-system rates and labor efforts are authored planning inputs. No installed supplier/contractor quotes exist.

## Rebuild and checks

Python 3.13 + Pillow; Blender 5.0.1 background factory startup. New plan generation uses the installed `room-first-building-study` skill's `building_study.framing.profile('us')`. Set `ROOM_FIRST_SKILL` to that skill root if different from `C:/Users/shaun/.codex/skills/room-first-building-study`. The generated SVG embeds the selected profile, so model/takeoff readers consume the checked-in actual source/profile without needing to regenerate plans.

```powershell
python scripts/owner_plan.py
python scripts/owner_project.py
& 'C:/Program Files/Blender Foundation/Blender 5.0/blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/owner_model.py
& 'C:/Program Files/Blender Foundation/Blender 5.0/blender.exe' --background --factory-startup --disable-autoexec revisions/owner-brief-v2/model/Owner-Earthship.blend --python-exit-code 1 --python scripts/owner_takeoff.py -- --render-stages
python scripts/owner_costs.py
python scripts/owner_site.py
python scripts/owner_checks.py
```

Checks cover exact source coverage/readback, unsupported/stale source rejection, conservative full door swings, fixture containment, connected 30 in furnished routes/interior pads, bed access, actual saved fixture footprints, source/native/PDF hashes, four retained scenes, positive closed meshes, unit scale, glulam section metrology, 14 reveal stages, budget arithmetic and current links. A 30 in walking square is a study input, not accessibility/code approval. No structural load/span, comprehensive clash, moisture, drainage or egress certification is implied.

Plan/model/takeoff/site outputs are derived and will refresh. Existing gate evidence, procurement fields, decision values and phase cash figures entered in CSV trackers are preserved by the generators. Review changes before pushing; initial-delivery checks intentionally expect the currently unverified approvals. Never place private approval documents in the public repository.

## History and hosting

[Superseded ranch snapshot](https://github.com/shusain/portal-earthship-home-design/tree/0bfb490bcc7c7243a7f34b08109b511e1aeab222) retains the earlier 64 x 34 ft / 3-bedroom plan, model and cost history. Root `plans/`, `model/`, most root material files and the original builder scripts are historical V1 artifacts; they are not the current owner brief. Old report/review HTML bookmarks lead to the current revision. Do not run legacy `build_site.py` or `build_costs.py` as the current workflow.

GitHub Pages serves repository root from main; `.nojekyll` preserves buildless assets. Images use intrinsic proportions. Native binary/SVG identities are preserved by `.gitattributes`. Browser state, local PDF runtime/rendering, Blender backups and the raw source PDF are ignored.
