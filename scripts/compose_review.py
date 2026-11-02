from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
ROOT=Path(__file__).resolve().parents[1]
labels=json.loads((ROOT/'model'/'assembly-receipt.json').read_text())['stages']
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
frames=[]
for stage in range(1,15):
    im=Image.open(ROOT/'review'/'stages'/f'{stage:02}.png').convert('RGB');d=ImageDraw.Draw(im);d.rectangle((0,0,im.width,45),fill='#243a35');d.text((18,10),f'{stage:02} / {labels[str(stage)]}',font=font,fill='white');frames.append(im)
frames[0].save(ROOT/'review'/'construction.gif',save_all=True,append_images=frames[1:],duration=[750]*13+[2400],loop=0)
sheet=Image.new('RGB',(960*2,645*2),'#faf7ef')
for i,(name,label) in enumerate([('exterior','South exterior / earth berm massing'),('cutaway','Furnished cutaway'),('floor-plan','Top view / source fixtures'),('structure','Structural reservations / not engineered')]):
    im=Image.open(ROOT/'review'/f'{name}.png').convert('RGB');im.thumbnail((960,600));x=(i%2)*960;y=(i//2)*645;sheet.paste(im,(x,y+45));ImageDraw.Draw(sheet).text((x+15,y+10),label,font=font,fill='#243a35')
sheet.save(ROOT/'review'/'overview.jpg',quality=92)
print('Saved construction.gif and overview.jpg')
