from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
N={"steps":"Steps / flow boxes","timeline":"Timeline","icons":"Icon count","chapter":"Chapter card","quote":"Quote card","screen":"App screen","document":"Document quote",
"statement":"Statement type","object":"Spinning object","article":"Article headline","chat":"Chat thread","search":"Search box","pie":"Donut / pie","squares":"Squares to scale",
"timer":"Countdown timer","receipt":"Receipt","animate":"Animated metaphor","clock":"Clock","calendar":"Calendar","sign":"Sign / banner","social":"Social post (labelled)",
"comments":"Comment thread","trending":"Trending list","stamp":"Stamp: FALSE","board":"Rules board","hero":"Hero disc","desk":"Desk with props","pinboard":"Evidence pinboard",
"opener":"Chapter opener","reveal":"Line reveal","clipping":"Newspaper clipping","bignumber":"Big number","seats":"Parliament seats","stack":"Object stacks","stand":"Figures on bars",
"fan":"Fanned cards","trend":"Picture line chart","slice":"Object pie slice","compare":"Then vs now","photoline":"Photo timeline","tv":"Old TV broadcast","tornsplit":"Torn split",
"newscard":"News card","blueprint":"Blueprint","pyramid":"Population pyramid","flowchart":"Money flowchart","linkmap":"Link map","orgchart":"Org chart","courtdoc":"Court document",
"table":"Table","interview":"Interview card","endcard":"End card","polltrack":"Poll tracker","area":"Area chart","candles":"Candlesticks","bars3d":"3D bars","prism":"3D prism map",
"explode":"Exploded view (3D)","title3d":"3D title","towers3d":"3D towers","photo":"Photo, 2.5D","photos":"Photo pair","photo3d":"Photo, 3D camera","myth":"Myth stamp","counter":"Counter",
"staircase":"Staircase","scale":"Balance scale","planets":"Planets to scale","units":"Unit squares","reel":"Reel","conveyor":"Conveyor","pile":"Pile of flags","grids":"Side-by-side grids","poster":"Collage poster"}
fs=sorted(Path("all").glob("*.jpg"))
big=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",28); small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",17)
for part,chunk in enumerate((fs[:37],fs[37:])):
    cols,w,h,lab=4,480,270,34; rows=(len(chunk)+cols-1)//cols
    s=Image.new("RGB",(cols*w,70+rows*(h+lab)),"#141414"); d=ImageDraw.Draw(s)
    d.text((20,18),f"VISUAL TYPES {part*37+1}–{part*37+len(chunk)} OF 74   ·   STYLE SAMPLES, ILLUSTRATIVE DATA",fill="#FFDD33",font=big)
    for i,f in enumerate(chunk):
        x,y=(i%cols)*w,70+(i//cols)*(h+lab)
        s.paste(Image.open(f).convert("RGB").resize((w-6,h-6)),(x+3,y+3))
        k=f.stem.split("_",1)[1]; d.text((x+8,y+h+6),f"{f.stem[:3]}  {N.get(k,k)}",fill="#EDEDED",font=small)
    s.save(f"visual_types_sheet_{part+1}.jpg",quality=86)
