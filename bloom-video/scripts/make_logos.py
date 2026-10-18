"""assets/ 원본 로고에서 배경을 제거해 public/logos/*.png(투명 배경)로 저장.
흰색 단색화는 화면에서 CSS filter로 처리한다."""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets"
DST = ROOT / "public" / "logos"


def knockout(src: Path, dst: Path) -> None:
    img = Image.open(src).convert("RGB")
    bg = img.getpixel((2, 2))  # 좌상단 = 배경색
    w, h = img.size
    out = Image.new("RGBA", (w, h))
    px, op = img.load(), out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            d = max(abs(r - bg[0]), abs(g - bg[1]), abs(b - bg[2]))
            a = max(0, min(255, int((d - 24) * 255 / 120)))
            op[x, y] = (r, g, b, a)
    out = out.crop(out.getbbox())
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)
    print(f"{src.name} -> {dst.relative_to(ROOT)} {out.size}")


for name in ("bloom", "oracle"):
    src = next(SRC.glob(f"logo_{name}.*"))
    knockout(src, DST / f"{name}.png")
