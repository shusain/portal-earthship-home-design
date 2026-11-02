# Earth Groundship — Portal, Arizona

**Selected layout A: 64′ × 34′, single-story, three bedrooms and two bathrooms.**

Start with [the GitHub Pages design overview](https://shusain.github.io/portal-earthship-home-design/), [the local overview](index.html), [the selected plan](plans/A-long-ranch.svg), or [the four-view overview](review/overview.jpg).

**Construction materials, labor and time:** [supplier-linked report](materials/costs.html), [Markdown document](materials/cost-breakdown.md), [house purchasing CSV](materials/us-purchasing-and-costs.csv), [labor / schedule CSV](materials/labor-and-schedule.csv), [labor options](materials/labor-options.csv), and [direct construction summary](materials/overall-budget.csv). Land and off-grid generation/storage are already acquired. House wiring/panel/protection remains included; no new power system or utility extension is budgeted. Supplier price benchmarks were researched November 2, 2026. Labor hours, billable rates and schedule assumptions are authored estimates, not local bids. Current totals are in [estimate.json](materials/estimate.json).

The main cost view now covers **house construction materials + trade labor + machinery/forms/pump/lift**. It compares owner-managed hired trades, owner-assisted partitions/interior finishes, and GC-coordinated hired trades. Professional fees, tax, freight and contingency are [separate planning items](materials/separate-budget-items.csv). The patio is optional; off-house water/septic systems are excluded and their existing status is unconfirmed. The dependency schedule starts after permit/procurement readiness and distinguishes person-hours, crew size, active work and waiting time.

The gross enclosed footprint is **2,175.94 sf**, including the exterior/partition walls. Conservative clear floor area is **1,914.18 sf**, excluding wall bands and door thresholds. This is a roughly 2,000 sf study, not exactly 2,000 sf gross. Patio, berms and roof overhangs are outside the house area. If 2,000 sf is a strict maximum enclosed area, the footprint needs a further reduction. The user selected A over compact alternative B on November 2, 2026.

## Design

The home faces south with an open walk-out yard. All three bedrooms have direct south-facing escape-window reservations. Living, kitchen and dining form an open west-side enclosure, with a continuous gallery connecting the rooms. Rear service rooms include laundry, shared bath, mechanical/pantry, primary bath and a walk-in closet. The primary bedroom, bath and closet share a suite vestibule; the vestibule currently has no privacy door to the main gallery. Mechanical equipment and food storage require separate cabinets/partitions at the detailed-design stage.

North and side walls are earth-bermed; the baseline roof is exposed, lightweight and slopes south at ¼″/ft. The section assumes approximately 6′ rear burial. This is an **earth-bermed ranch**, with earthship-inspired thermal mass and passive-solar orientation. Tire walls, greenhouse, soil-covered roof and off-grid autonomy have not been specified. The south yard must stay open for bedroom escape; a future greenhouse cannot obstruct those paths.

Nominal ceiling height is 9′; finish below the ceiling substrate and the dropped public-area transfer beam reduce local clearance. The modeled beam underside is approximately **7′10″**. It is an engineering reservation, not a verified member. Exterior assembly totals approximately 12″; partitions are 4½″. Plan datums use integer millimetres for consistent topology. **Lumber is defined in exact US dressed inches:** nominal 2×4 = actual 1½″ × 3½″; nominal 2×6 = actual 1½″ × 5½″. Stud spacing is exactly 16″ on center. Two-ply 2×6 schematic headers have a ½″ plywood spacer and are separately measured. All published purchasing/takeoff volumes and quantities use US units. Integer-mm plan coordinates and Blender's internal metre coordinates are computational units, not material stock sizes.

## Deliverables

- [Selected semantic floor plan](plans/A-long-ranch.svg), [room areas](plans/A-long-ranch-rooms.csv), [alternative B](plans/B-compact-ranch.svg), [section/site intent](plans/section-and-site.svg).
- [Native Blender file](model/Earth-Groundship.blend): construction sequence, furnished cutaway, floor plan and structural scenes. Imperial display units; geometry in metres. Timeline stages start at frames 1, 11, …, 131; complete frame 151. These are assembly visibility reveals, not a simulated construction operation.
- [Construction animation](review/construction.gif), [exterior](review/exterior.png), [cutaway](review/cutaway.png), [structure](review/structure.png).
- [Bill of materials CSV](materials/bill-of-materials.csv), [takeoff notes](materials/README.md), [per-component quantities](materials/components.csv), [machine-readable takeoff](materials/quantities.json).
- [Code/site research](research/code-and-site-basis.md), [plan checks](plans/A-long-ranch-validation.json), [furnished routing checks](plans/A-long-ranch-routes.json), [native readback](model/native-readback.json).

The quantity report distinguishes modeled geometry, schematic reservations and purchasing allowances. Reinforcement, structural connections, surveyed earthwork, complete building services and site systems remain unengineered. Cost allowances reserve money for those items without inventing measured quantities. Furniture placeholders do not become material consumption. The raw model takeoff retains the patio reservation, while the house purchasing/cost headline excludes it. The dated cost report separates advertised material benchmarks, authored trade person-hours/rates, machinery, optional GC fees and separately scoped planning items. It is not a bid, a local supplier quote, a guaranteed project budget or an order-ready cut list.

## Verified and unresolved

Checks cover exact disjoint room coverage, derived wall ownership, source-SVG readback and SHA256 identity, source fixture containment, conservative complete door-swing boxes, connected 30″ square furnished routes, interior door pads, both bed sides/foot access, and approximately 49½″ clear main corridor width. The 30″ route envelope is a study input, not an accessibility standard. External door pads/landings and product-certified clear opening dimensions remain unresolved.

Native-file checks reopen the saved model and verify unique original component IDs, closed positive-volume meshes, finite coordinates, unit scales, four retained review scenes and all 14 source-scene reveal stages. They do not certify structure, code compliance, daylight/ventilation performance, drainage, comprehensive clashes or construction readiness. Renders are from the native geometry.

Cochise County adopted 2024 residential codes effective September 1, 2026, along with 2023 NEC and retained 2012 IECC, subject to local amendments. The parcel jurisdiction, current amendments/design loads, survey, groundwater/flood constraints, retaining-wall reinforcement and roof design must be confirmed. See the linked research for primary sources and retrieval limitations. This study is **not for construction**.

## Reproduce locally

Uses Python 3.13, Pillow, and installed Blender 5.0.1. No skill-library runtime dependency or add-ons. Run from this directory in PowerShell:

```powershell
python scripts/design.py
python scripts/check_routes.py
& 'C:/Program Files/Blender Foundation/Blender 5.0/blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/build_model.py
& 'C:/Program Files/Blender Foundation/Blender 5.0/blender.exe' --background --factory-startup --disable-autoexec model/Earth-Groundship.blend --python-exit-code 1 --python scripts/verify_takeoff.py
& 'C:/Program Files/Blender Foundation/Blender 5.0/blender.exe' --background --factory-startup --disable-autoexec model/Earth-Groundship.blend --python-exit-code 1 --python scripts/render_stages.py
python scripts/compose_review.py
python scripts/check_source_rejection.py
python scripts/build_costs.py
python scripts/build_site.py
python scripts/check_delivery.py
```

Reproduction refreshes the generated study outputs. Copy a revision into a new directory before changing the reviewed source. The builder consumes actual SVG rooms, boundaries, hosted openings and fixture rectangles; stale wall cells and unsupported source transforms are rejected. Quantities record both source and native-file SHA256 hashes and never resave the native model. The optional browser screenshot is only review evidence and is not a geometry source.

## GitHub Pages publication

Repository: <https://github.com/shusain/portal-earthship-home-design>. Public overview: <https://shusain.github.io/portal-earthship-home-design/>. Pages serves the repository root from `main`; `.nojekyll` keeps the buildless HTML/SVG/download site intact. `scripts/build_site.py` refreshes the overview from the cost estimate and native validation receipt. After changing the design, rerun the model/takeoff/review/cost/site checks before committing and pushing. Browser profiles, Blender backup files and local runtime state are ignored and are not publication artifacts.
