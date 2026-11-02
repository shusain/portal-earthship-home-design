from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
s=bpy.data.scenes['01 Construction sequence'];s.render.resolution_x=960;s.render.resolution_y=600;s.cycles.samples=8
(ROOT/'review'/'stages').mkdir(exist_ok=True)
for stage in range(1,15):
    s.frame_set((stage-1)*10+1);s.render.filepath=str(ROOT/'review'/'stages'/f'{stage:02}.png');bpy.ops.render.render(write_still=True,scene=s.name)
print('14 STAGE RENDERS COMPLETE; native file unchanged')
