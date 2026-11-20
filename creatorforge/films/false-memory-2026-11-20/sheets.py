"""Contact sheets for the owner: two columns of 960x540 stills, eight to a sheet, each named. Run after shoot_http.py."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

D = Path(__file__).resolve().parent
OUT = D / "sheets"; OUT.mkdir(exist_ok=True)
FONT = "/home/user/forgeos/creatorforge/worker/creatorforge_worker/media/vendor/fonts"
try:
    F = ImageFont.truetype(next(Path(FONT).glob("*.ttf")).as_posix(), 22)
except Exception:
    F = ImageFont.load_default()


def stills(tag="FM", per=8):
    names = sorted(p.stem for p in (D / "html").glob("*.html") if p.stem[:2].isdigit())   # key frames only (01_hook ...); the video's own pages (m_, t_, r_, v_) are not key frames
    for old in OUT.glob(f"{tag}_*.jpg"):
        old.unlink()
    for k in range(0, len(names), per):
        part = names[k:k + per]; rows = (len(part) + 1) // 2
        S = Image.new("RGB", (2 * 960 + 30, rows * 580 + 10), "#0B0D14"); d = ImageDraw.Draw(S)
        for i, n in enumerate(part):
            im = Image.open(D / "png" / f"{n}.jpg").convert("RGB").resize((960, 540), Image.LANCZOS)
            x, y = 10 + (i % 2) * 970, 10 + (i // 2) * 580
            S.paste(im, (x, y)); d.text((x + 4, y + 544), n, fill="#F0F4F8", font=F)
        S.save(OUT / f"{tag}_{k // per + 1:02d}.jpg", quality=86)
    print("sheets for", len(names), "frames")


if __name__ == "__main__":
    stills()
