"""Map fly-ins, the documentary "Google Earth" move: the camera starts over India, swoops down and tilts into the
place the line is about, pins drop in with their names, and a route between places draws itself across the map.

    Fly: Kota | जहाँ से शुरू हुआ
    Fly: Delhi → Khanauri | किसानों का रास्ता
    Fly: Delhi=दिल्ली → Mandi=मंडी        (a name shown in Hindi: "lookup name=label")

Drawn with MapLibre GL JS (BSD-3-Clause, vendored) in headless Chromium, frame by frame. On the pod the map is real
OpenStreetMap data (© OpenStreetMap contributors, tiles from OpenFreeMap) - roads, rivers, cities. Without internet
the same flight runs over CreatorForge's own world map (Natural Earth, public domain). Places come from the bundled
world.json, then OpenStreetMap's Nominatim geocoder (cached); a place it cannot find leaves the line on its picture."""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

from .ff import MediaError

VENDOR = Path(__file__).parent / "vendor"
STYLE_URL = os.environ.get("CF_MAP_STYLE", "https://tiles.openfreemap.org/styles/liberty")
GEO_CACHE = Path(os.environ.get("CF_GEO_CACHE", Path.home() / ".cache" / "creatorforge" / "geocode.json"))
ACCENT = {"investigative": "#C8102E", "editorial": "#E8B400"}


def _online(url: str, timeout: float = 4.0) -> bool:
    try:
        urllib.request.urlopen(urllib.request.Request(url, method="GET", headers={"User-Agent": "CreatorForge"}),
                               timeout=timeout).close()
        return True
    except Exception:  # noqa: BLE001
        return False


def _cache() -> dict:
    try:
        return json.loads(GEO_CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def geocode(name: str) -> tuple[float, float] | None:
    """(lat, lon) for a place name: the bundled world map first, then OpenStreetMap's geocoder (cached)."""
    from . import maps
    f = maps._find(name)
    if f and f["kind"] == "city":
        return f["lat"], f["lon"]
    if f and f["kind"] == "country":
        pts = [p for ring in f["rings"] for p in ring]
        lons, lats = [p[0] for p in pts], [p[1] for p in pts]
        return (min(lats) + max(lats)) / 2, (min(lons) + max(lons)) / 2
    key = name.strip().lower()
    c = _cache()
    if key in c:
        return tuple(c[key]) if c[key] else None
    if os.environ.get("CF_GEOCODE", "1") == "0":
        return None
    try:
        q = urllib.parse.urlencode({"q": name, "format": "json", "limit": 1, "countrycodes": "in"})
        req = urllib.request.Request(f"https://nominatim.openstreetmap.org/search?{q}",
                                     headers={"User-Agent": "CreatorForge/1.0 (video explainer maps)"})
        rows = json.loads(urllib.request.urlopen(req, timeout=8).read())
        if not rows:            # not in India: search the whole world
            req = urllib.request.Request(req.full_url.replace("&countrycodes=in", ""), headers=req.headers)
            rows = json.loads(urllib.request.urlopen(req, timeout=8).read())
        hit = (float(rows[0]["lat"]), float(rows[0]["lon"])) if rows else None
    except Exception:  # noqa: BLE001 - no internet: the line keeps its picture
        return None
    c[key] = list(hit) if hit else None
    GEO_CACHE.parent.mkdir(parents=True, exist_ok=True)
    GEO_CACHE.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    return hit


def parse(spec: str) -> dict | None:
    head, _, title = (spec or "").partition("|")
    parts = [x.strip() for x in re.split(r"→|->", head) if x.strip()][:5]
    if not parts:
        return None
    places = []
    for p in parts:
        look, _, label = p.partition("=")
        ll = geocode(look.strip())
        if ll is None:
            return None                     # a place we cannot put on the map: the line keeps its picture
        places.append({"name": (label or look).strip(), "lat": ll[0], "lon": ll[1]})
    return {"places": places, "route": len(places) >= 2, "title": title.strip()}


def _offline_style(theme: str) -> dict:
    """A style with no internet: CreatorForge's own world map (land, borders), India highlighted."""
    from . import maps
    feats = []
    for c in maps._world()["countries"]:
        polys = [[ring + ([ring[0]] if ring and ring[0] != ring[-1] else [])] for ring in c["r"] if len(ring) >= 3]
        if polys:
            feats.append({"type": "Feature", "properties": {"name": c["n"], "india": c["n"] == "India"},
                          "geometry": {"type": "MultiPolygon", "coordinates": polys}})
    land = {"type": "FeatureCollection", "features": feats}
    acc = ACCENT.get(theme, "#C8102E")
    return {"version": 8, "sources": {"land": {"type": "geojson", "data": land}},
            "layers": [{"id": "sea", "type": "background", "paint": {"background-color": "#B9C9CF"}},
                       {"id": "land", "type": "fill", "source": "land",
                        "paint": {"fill-color": ["case", ["get", "india"], "#EFE3C6", "#E2DCCB"]}},
                       {"id": "india", "type": "line", "source": "land", "filter": ["get", "india"],
                        "paint": {"line-color": acc, "line-width": 2.2}},
                       {"id": "borders", "type": "line", "source": "land",
                        "paint": {"line-color": "#8C7F66", "line-width": 0.6}}]}


_PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><style>%CSS%
html,body,#m{margin:0;padding:0;width:%W%px;height:%H%px;overflow:hidden;background:#cfd8dc}
.pin{position:absolute;transform:translate(-50%,-100%);font-family:'FreeSans','Noto Sans Devanagari','DejaVu Sans',sans-serif;
 font-weight:700;color:#fff;background:%ACC%;padding:.25em .6em;border-radius:.35em;white-space:nowrap;
 font-size:%FS%px;box-shadow:0 .2em .6em rgba(0,0,0,.35);opacity:0}
.pin:after{content:'';position:absolute;left:50%;bottom:-.45em;margin-left:-.45em;border:.45em solid transparent;border-bottom:0;border-top-color:%ACC%}
.dot{position:absolute;width:%DOT%px;height:%DOT%px;margin:-%DOTH%px 0 0 -%DOTH%px;border-radius:50%;background:%ACC%;
 border:3px solid #fff;box-shadow:0 0 0 0 rgba(200,16,46,.6);opacity:0}
#title{position:absolute;left:50%;top:%TOP%px;transform:translateX(-50%);font-family:'FreeSans','Noto Sans Devanagari','DejaVu Sans',sans-serif;
 font-weight:700;font-size:%TFS%px;color:#fff;background:rgba(15,18,24,.78);padding:.3em .8em;border-radius:.3em;opacity:0;white-space:nowrap}
#credit{position:absolute;right:12px;bottom:10px;font:600 %CFS%px 'DejaVu Sans',sans-serif;color:rgba(20,20,20,.75);
 background:rgba(255,255,255,.65);padding:2px 6px;border-radius:3px}
</style><script>%JS%</script></head><body><div id="m"></div><div id="title"></div><div id="credit">%CREDIT%</div><script>
const P=%PLAN%, DUR=%DUR%;
const map=new maplibregl.Map({container:'m',style:%STYLE%,interactive:false,attributionControl:false,
  preserveDrawingBuffer:true,fadeDuration:0,center:[P.places[0].lon,P.places[0].lat],zoom:4,pitch:0,bearing:0});
const pins=P.places.map(p=>{const d=document.createElement('div');d.className='dot';document.body.appendChild(d);
  const l=document.createElement('div');l.className='pin';l.textContent=p.name;document.body.appendChild(l);return {d,l,p}});
const tt=document.getElementById('title'); tt.textContent=P.title||''; if(!P.title)tt.style.display='none';
const E=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2, C=(a,b,t)=>a+(b-a)*t, cl=x=>Math.max(0,Math.min(1,x));
let route=[];
function densify(){const out=[];for(let i=0;i<P.places.length-1;i++){const a=P.places[i],b=P.places[i+1];
  for(let k=0;k<60;k++){const t=k/60;out.push([C(a.lon,b.lon,t),C(a.lat,b.lat,t)])}}const z=P.places[P.places.length-1];out.push([z.lon,z.lat]);return out}
let endCam;
map.on('load',()=>{
  map.addSource('route',{type:'geojson',data:{type:'Feature',geometry:{type:'LineString',coordinates:[]}}});
  map.addLayer({id:'route-glow',type:'line',source:'route',paint:{'line-color':'#ffffff','line-width':10,'line-opacity':.7},layout:{'line-cap':'round','line-join':'round'}});
  map.addLayer({id:'route',type:'line',source:'route',paint:{'line-color':'%ACC%','line-width':5},layout:{'line-cap':'round','line-join':'round'}});
  route=densify();
  if(P.places.length>1){const b=new maplibregl.LngLatBounds();P.places.forEach(p=>b.extend([p.lon,p.lat]));
    endCam=map.cameraForBounds(b,{padding:{top:%H%*0.22,bottom:%H%*0.18,left:%W%*0.15,right:%W%*0.15}});
    endCam={center:[endCam.center.lng,endCam.center.lat],zoom:Math.min(endCam.zoom,11)};}
  else endCam={center:[P.places[0].lon,P.places[0].lat],zoom:%ZEND%};
  window.READY=true;
});
function settle(){return new Promise(r=>{let done=false;const go=()=>{if(!done){done=true;r()}};
  if(map.loaded()&&map.areTilesLoaded()){requestAnimationFrame(()=>requestAnimationFrame(go))}else{map.once('idle',go)}
  setTimeout(go,%WAIT%)})}
window.frame=async function(t){
  const s=t/DUR, india=[78.9,22.6];
  const fly=E(cl(s/0.55));                                     // 0..55%: the swoop down from India-wide
  const c0=india, c1=endCam.center;
  const center=[C(c0[0],c1[0],fly),C(c0[1],c1[1],fly)];
  const hop=Math.sin(Math.PI*fly)*0.6;                          // a gentle rise mid-flight, like a real fly-to
  const zoom=C(4.1,endCam.zoom,fly)-hop+0.35*E(cl((s-0.6)/0.4));
  map.jumpTo({center,zoom,pitch:C(0,52,E(cl(s/0.7))),bearing:C(0,-12,E(cl(s)))});
  const drawn=cl((s-0.45)/0.4);
  if(route.length&&P.places.length>1){const n=Math.max(2,Math.floor(route.length*drawn));
    map.getSource('route').setData({type:'Feature',geometry:{type:'LineString',coordinates:drawn>0?route.slice(0,n):[]}})}
  await settle();
  pins.forEach((x,i)=>{const at=P.places.length>1?0.45+0.4*(i/(P.places.length-1)):0.5;const k=cl((s-at)/0.12);
    const q=map.project([x.p.lon,x.p.lat]);x.d.style.left=q.x+'px';x.d.style.top=q.y+'px';x.d.style.opacity=k;
    x.l.style.left=q.x+'px';x.l.style.top=(q.y-%DOT%*0.9-(1-k)*20)+'px';x.l.style.opacity=k;
    x.d.style.boxShadow=`0 0 0 ${(1-k)*30}px rgba(200,16,46,${0.5*(1-k)})`});
  tt.style.opacity=cl((s-0.05)/0.15);
};
</script></body></html>"""


def render(plan: dict, theme: str, width: int, height: int, seconds: float, out: Path, work: Path,
           fps: int | None = None) -> Path:
    from . import motion
    if not motion.enabled():
        raise MediaError("fly-in: no Chromium/Playwright")
    fps = int(fps or (60 if os.environ.get("CF_FPS") == "60" else 30))
    online = os.environ.get("CF_MAP_OFFLINE") != "1" and _online(STYLE_URL)
    style = json.dumps(STYLE_URL) if online else json.dumps(_offline_style(theme))
    credit = "© OpenStreetMap contributors · OpenFreeMap" if online else "Map: Natural Earth"
    u = min(width, height)
    page = (_PAGE.replace("%CSS%", (VENDOR / "maplibre-gl.css").read_text(encoding="utf-8"))
            .replace("%JS%", (VENDOR / "maplibre-gl.js").read_text(encoding="utf-8"))
            .replace("%PLAN%", json.dumps(plan, ensure_ascii=False)).replace("%STYLE%", style)
            .replace("%DUR%", f"{seconds:.3f}").replace("%W%", str(width)).replace("%H%", str(height))
            .replace("%ACC%", ACCENT.get(theme, "#C8102E")).replace("%FS%", str(int(u * 0.034)))
            .replace("%TFS%", str(int(u * 0.042))).replace("%TOP%", str(int(height * 0.08)))
            .replace("%CFS%", str(max(11, int(u * 0.016)))).replace("%DOT%", str(int(u * 0.028)))
            .replace("%DOTH%", str(int(u * 0.014))).replace("%CREDIT%", credit)
            .replace("%ZEND%", "11.5").replace("%WAIT%", "6000" if online else "400"))
    work.mkdir(parents=True, exist_ok=True)
    html = work / f"fly_{out.stem}.html"
    html.write_text(page, encoding="utf-8")
    frames = max(2, int(round(seconds * fps)))
    from playwright.sync_api import sync_playwright
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps),
                            "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                            "-pix_fmt", "yuv420p", "-r", str(fps), str(out)], stdin=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    try:
        with sync_playwright() as p:
            browser = motion._launch(p)
            try:
                pg = browser.new_page(viewport={"width": width, "height": height})
                errors: list[str] = []
                pg.on("pageerror", lambda e: errors.append(str(e)))
                pg.goto(html.as_uri())
                pg.wait_for_function("window.READY === true", timeout=60000)
                for i in range(frames):
                    pg.evaluate(f"window.frame({i / fps:.4f})")
                    enc.stdin.write(pg.screenshot(type="jpeg", quality=92))
                if errors:
                    raise MediaError(f"fly-in page error: {errors[0][:200]}")
            finally:
                browser.close()
        enc.stdin.close()
        if enc.wait(timeout=600) != 0:
            raise MediaError("fly-in encode failed")
    except MediaError:
        enc.kill()
        raise
    except Exception as e:  # noqa: BLE001 - the pipeline keeps the flat map or the picture
        enc.kill()
        raise MediaError(f"fly-in failed: {e}") from None
    return out
