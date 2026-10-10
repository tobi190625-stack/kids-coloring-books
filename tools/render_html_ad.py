#!/usr/bin/env python3
"""Conversion ads rendered as HTML/CSS motion graphics in a real browser (Playwright/Chromium).

A different pipeline from the PIL renderers: the ad is a web page with CSS 3D and keyframe animations
(a 3D book that opens and turns its real pages, benefit chips, a "Tap the link" call to action).
The script pauses every animation, steps the clock frame by frame, screenshots each frame and
encodes them with ffmpeg; then adds Kokoro voice + music (tools/voice.py).

Usage: python3 tools/render_html_ad.py <book> <out.mp4> [--yt]     book = nico | benny | rocco | posy
Built for conversion: cover + hook on frame 1 (best FB result so far), proof (real pages, one colored),
then a clear "Tap the link" ending (Reels with Meta Verified carry a link; --yt says "link in description").
"""
import base64
import io
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import paint  # noqa: E402
import voice  # noqa: E402
from make_video import find_cover  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS, T = 1080, 1920, 30, 15.0
BOOKS = {
    "nico": dict(dir="books/003-nico-the-reindeer", pages=[8, 13], color=17, music="nico-soft",
                 bg=("#EAF4FD", "#C9E2F7"), accent="#D9483B", spine="#B5352B",
                 hook="Got a little one who loves Christmas?", name="Nico",
                 lines=["Got a little one who loves Christmas?", "Meet Nico, the little reindeer.",
                        "Your kid colors every page, and reads the story.", "One big picture. One easy sentence.",
                        "Tap the link to get it on Amazon."]),
    "benny": dict(dir="books/002-benny-the-bear/kdp-8.5x8.5", pages=[5, 16], color=20, music="benny-soft",
                  bg=("#FFF4E0", "#FBDDB0"), accent="#E58A2E", spine="#B9651B",
                  hook="Got a little one who loves cuddly bears?", name="Benny",
                  lines=["Got a little one who loves cuddly bears?", "Meet Benny, the bear.",
                         "Your kid colors every page, and reads the story.", "One big picture. One easy sentence.",
                         "Tap the link to get it on Amazon."]),
    "rocco": dict(dir="books/005-rocco-monster-truck", pages=[9, 10], color=25, music="rocco-upbeat",
                  bg=("#EAF6FF", "#BFE0FA"), accent="#2F7FD1", spine="#1F5C9E",
                  hook="Got a little one who loves monster trucks?", name="Rocco",
                  lines=["Got a little one who loves monster trucks?", "Meet Rocco, the littlest monster truck.",
                         "Your kid colors every page, and reads the story.", "One big picture. One easy sentence.",
                         "Tap the link to get it on Amazon."]),
    "posy": dict(dir="books/006-posy-the-unicorn", pages=[4, 25], color=31, music="marimba-sunny",
                 bg=("#FDEEF6", "#EBD5F7"), accent="#C25BB0", spine="#9A3F8B",
                 hook="Got a little one who loves unicorns?", name="Posy",
                 lines=["Got a little one who loves unicorns?", "Meet Posy, the little unicorn.",
                        "Your kid colors every page, and reads the story.", "One big picture. One easy sentence.",
                        "Tap the link to get it on Amazon."]),
}
LINE_T = [0.15, 3.0, 5.4, 9.0, 11.6]  # when each voice line starts (s)


def uri(img, fmt="JPEG"):
    buf = io.BytesIO()
    img.convert("RGB").save(buf, fmt, quality=90)
    return f"data:image/{fmt.lower()};base64," + base64.b64encode(buf.getvalue()).decode()


def pdf_page(book_dir, n, px=900):
    import pymupdf
    pg = pymupdf.open(book_dir / "out" / "interior.pdf")[n - 1]
    pix = pg.get_pixmap(dpi=int(px / pg.rect.width * 72))
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples).resize((px, px))


def assets(cfg):
    bd = ROOT / cfg["dir"]
    img, labels, _, _ = paint.regions(bd, cfg["color"])
    col = Image.fromarray(paint.paint_full(img, labels, paint.load_map(bd, cfg["color"]))).resize((900, 900))
    bw = Image.fromarray(img if img.ndim == 3 else np.stack([img] * 3, -1)).resize((900, 900))
    return dict(cover=uri(find_cover(bd).resize((900, 900))), p1=uri(pdf_page(bd, cfg["pages"][0])),
                p2=uri(pdf_page(bd, cfg["pages"][1])), bw=uri(bw), col=uri(col))


def html(cfg, a, yt):
    font = base64.b64encode((ROOT / "fonts" / "Grandstander-ExtraBold.ttf").read_bytes()).decode()
    cta_small = "link in the description" if yt else "Find it on Amazon"
    caps = "".join(f'<div class="cap" style="animation-delay:{t}s">{ln}</div>' for t, ln in zip(LINE_T, cfg["lines"]))
    # every animation has duration/delay in seconds; the renderer sets currentTime on each frame
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:G;src:url(data:font/ttf;base64,{font})}}
*{{box-sizing:border-box;margin:0}}
body{{width:{W}px;height:{H}px;overflow:hidden;font-family:G,sans-serif;color:#2E3A55;
 background:radial-gradient(120% 80% at 50% 30%,{cfg['bg'][0]},{cfg['bg'][1]})}}
.hook{{position:absolute;top:150px;left:70px;right:70px;text-align:center;font-size:84px;line-height:1.05;
 animation:hookOut .4s 2.7s both}}
.hook b{{color:{cfg['accent']}}}
@keyframes hookOut{{to{{opacity:0;transform:translateY(-40px)}}}}
.stage{{position:absolute;left:0;right:0;top:430px;height:900px;perspective:2600px;animation:stageMove 1s 10.6s both}}
@keyframes stageMove{{to{{transform:translateY(-170px) scale(.78)}}}}
.book{{position:absolute;left:150px;top:30px;width:780px;height:780px;transform-style:preserve-3d;
 animation:float 3s 0s both, face .7s 2.6s both}}
@keyframes float{{from{{transform:rotateY(-28deg) rotateX(8deg) translateY(30px) scale(.9)}}to{{transform:rotateY(-22deg) rotateX(6deg) translateY(0) scale(.95)}}}}
@keyframes face{{from{{transform:rotateY(-22deg) rotateX(6deg) scale(.95)}}to{{transform:rotateY(0) rotateX(0) scale(1)}}}}
.page,.leaf{{position:absolute;inset:0;background:#fff;border-radius:6px 16px 16px 6px;overflow:hidden;
 box-shadow:0 30px 60px rgba(40,50,80,.28)}}
.page img,.leaf img{{width:100%;height:100%;display:block}}
.spine{{position:absolute;left:-36px;top:0;width:36px;height:100%;background:{cfg['spine']};transform-origin:right;
 transform:rotateY(-90deg);border-radius:6px 0 0 6px}}
.leaf{{transform-origin:left center;backface-visibility:hidden}}
.cover{{animation:open 1s 3.3s both}}
.l1{{animation:open .9s 5.6s both}}
.l2{{animation:open .9s 7.4s both}}
@keyframes open{{to{{transform:rotateY(-178deg)}}}}
.colorize{{position:absolute;inset:0;clip-path:inset(0 100% 0 0);animation:wipe 1.6s 8.2s both}}
@keyframes wipe{{to{{clip-path:inset(0 0 0 0)}}}}
.chips{{position:absolute;left:60px;right:60px;top:1360px;display:flex;justify-content:center;gap:22px;flex-wrap:wrap}}
.chip{{background:#fff;border-radius:60px;padding:18px 34px;font-size:46px;box-shadow:0 8px 20px rgba(40,50,80,.15);
 animation:pop .35s both}}
.chip:nth-child(1){{animation-delay:8.9s}}.chip:nth-child(2){{animation-delay:9.2s}}.chip:nth-child(3){{animation-delay:9.5s}}
@keyframes pop{{from{{transform:scale(0);opacity:0}}to{{transform:scale(1);opacity:1}}}}
.chips{{animation:chipsOut .4s 10.6s both}}
@keyframes chipsOut{{to{{opacity:0}}}}
.cta{{position:absolute;left:60px;right:60px;top:1150px;text-align:center;animation:pop .5s 11.1s both}}
.cta .big{{display:inline-block;background:{cfg['accent']};color:#fff;font-size:92px;padding:26px 60px;border-radius:90px;
 box-shadow:0 14px 30px rgba(40,50,80,.25)}}
.cta .small{{margin-top:26px;font-size:50px}}
.arrow{{position:absolute;left:120px;top:1390px;font-size:150px;color:{cfg['accent']};opacity:0;
 animation:show .01s 11.3s forwards, bob .6s 11.4s 6 alternate both}}
@keyframes show{{to{{opacity:1}}}}
@keyframes bob{{from{{transform:translateY(0)}}to{{transform:translateY(40px)}}}}
.title{{position:absolute;top:170px;left:70px;right:70px;text-align:center;font-size:70px;line-height:1.1;opacity:0;
 animation:show .4s 3.0s forwards}}
.title small{{display:block;font-size:44px;color:{cfg['accent']};margin-top:10px}}
.cap{{position:absolute;left:70px;right:70px;top:1560px;text-align:center;font-size:44px;line-height:1.2;background:rgba(255,255,255,.92);
 padding:16px 24px;border-radius:26px;opacity:0;animation:cap 2.6s both}}
@keyframes cap{{0%{{opacity:0}}6%{{opacity:1}}90%{{opacity:1}}100%{{opacity:0}}}}
</style></head><body>
<div class="hook">{cfg['hook'].replace('loves ', 'loves <b>').replace('?', '</b>?')}</div>
<div class="title">Color it. Then read it.<small>{cfg['name']}'s story book · ages 3-6</small></div>
<div class="stage"><div class="book">
  <div class="page"><img src="{a['bw']}"><div class="colorize"><img src="{a['col']}"></div></div>
  <div class="leaf l2"><img src="{a['p2']}"></div>
  <div class="leaf l1"><img src="{a['p1']}"></div>
  <div class="leaf cover"><img src="{a['cover']}"></div>
  <div class="spine"></div>
</div></div>
<div class="chips"><div class="chip">🖍️ Color it</div><div class="chip">📖 Read it</div><div class="chip">Ages 3-6</div></div>
<div class="cta"><div class="big">Tap the link</div><div class="small">{cta_small}</div></div>
<div class="arrow">⬇</div>
{caps}
</body></html>"""


def render(book, out, yt=False):
    cfg = BOOKS[book]
    page_html = html(cfg, assets(cfg), yt)
    tmp = Path(out).with_suffix(".silent.mp4")
    from playwright.sync_api import sync_playwright
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    enc = subprocess.Popen([ff, "-loglevel", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-crf", "21", "-pix_fmt", "yuv420p", str(tmp)], stdin=subprocess.PIPE)
    with sync_playwright() as p:
        exe = next((str(x) for x in [Path("/opt/pw-browsers/chromium")] if x.exists()), None)
        br = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        pg = br.new_page(viewport={"width": W, "height": H})
        pg.set_content(page_html, wait_until="load")
        pg.evaluate("document.fonts.ready")
        pg.evaluate("document.getAnimations().forEach(a=>a.pause())")
        for i in range(int(T * FPS)):
            pg.evaluate(f"document.getAnimations().forEach(a=>a.currentTime={i * 1000 / FPS})")
            enc.stdin.write(pg.screenshot(type="jpeg", quality=92))
        br.close()
    enc.stdin.close()
    enc.wait()
    lines = [(t, ln.replace("Tap the link to get it on Amazon.", "The link is in the description.") if yt else ln)
             for t, ln in zip(LINE_T, cfg["lines"])]
    voice.mix_into_video(tmp, voice.place(lines, T), ROOT / "marketing" / "music" / f"{cfg['music']}.wav", out,
                         music_vol=0.16)
    tmp.unlink()
    print("✓", out)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--yt"]
    if len(args) != 2 or args[0] not in BOOKS:
        sys.exit(__doc__)
    render(args[0], args[1], "--yt" in sys.argv)
