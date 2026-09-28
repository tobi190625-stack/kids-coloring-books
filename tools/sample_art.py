# Generates the SVG line art for books/001-leo-the-lion (kept as an example of drawing art in code).
import math
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent / "books/001-leo-the-lion/art"
S = 'stroke="#000" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"'

def svg(body, w=800, h=600):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n{body}\n</svg>\n'

def circle(cx, cy, r, fill="#fff"):
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" {S}/>'

def ellipse(cx, cy, rx, ry, fill="#fff"):
    return f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}" {S}/>'

def path(d, fill="none"):
    return f'<path d="{d}" fill="{fill}" {S}/>'

def eyes(cx, cy, dx, r=10):
    return circle(cx-dx, cy, r, "#000") + circle(cx+dx, cy, r, "#000")

def lion(cx, cy, s=1.0, mouth="smile"):
    p = []
    for i in range(14):
        a = 2*math.pi*i/14
        p.append(circle(cx+135*s*math.cos(a), cy+135*s*math.sin(a), 52*s))
    p.append(circle(cx-78*s, cy-88*s, 30*s))
    p.append(circle(cx+78*s, cy-88*s, 30*s))
    p.append(circle(cx, cy, 118*s))
    p.append(eyes(cx, cy-25*s, 40*s, 11*s))
    p.append(ellipse(cx, cy+40*s, 55*s, 38*s))
    p.append(path(f"M{cx-18*s:.0f},{cy+18*s:.0f} L{cx+18*s:.0f},{cy+18*s:.0f} L{cx:.0f},{cy+38*s:.0f} Z", "#000"))
    if mouth == "smile":
        p.append(path(f"M{cx-25*s:.0f},{cy+55*s:.0f} Q{cx:.0f},{cy+75*s:.0f} {cx+25*s:.0f},{cy+55*s:.0f}"))
    elif mouth == "small":
        p.append(circle(cx, cy+60*s, 8*s))
    else:
        p.append(ellipse(cx, cy+62*s, 30*s, 22*s, "#fff"))
    return "\n".join(p)

def sun(cx, cy, r):
    p = []
    for i in range(10):
        a = 2*math.pi*i/10
        p.append(path(f"M{cx+(r+15)*math.cos(a):.0f},{cy+(r+15)*math.sin(a):.0f} L{cx+(r+50)*math.cos(a):.0f},{cy+(r+50)*math.sin(a):.0f}"))
    p.append(circle(cx, cy, r))
    return "\n".join(p)

def star(cx, cy, r):
    pts = []
    for i in range(10):
        a = -math.pi/2 + math.pi*i/5
        rr = r if i % 2 == 0 else r*0.45
        pts.append(f"{cx+rr*math.cos(a):.0f},{cy+rr*math.sin(a):.0f}")
    return path("M" + " L".join(pts) + " Z", "#fff")

def grass(y, w=800):
    d = f"M20,{y}"
    for x in range(20, w-20, 40):
        d += f" Q{x+20},{y-35} {x+40},{y}"
    return path(d)

def bubble(x, y, w, h, text, size):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="40" fill="#fff" {S}/>'
            + path(f"M{x+40},{y+h} L{x+10},{y+h+50} L{x+90},{y+h}", "#fff")
            + f'<rect x="{x+34}" y="{y+h-6}" width="62" height="12" fill="#fff"/>'
            + f'<text x="{x+w/2}" y="{y+h/2+size/3}" font-family="Helvetica" font-weight="bold" font-size="{size}" text-anchor="middle" fill="#000">{text}</text>')

def tree(x, base, h):
    return (f'<rect x="{x-35}" y="{base-h}" width="70" height="{h}" fill="#fff" {S}/>'
            + circle(x-90, base-h, 90) + circle(x+90, base-h, 90) + circle(x, base-h-70, 110))

# 1 Leo in the jungle
(OUT/"01-leo.svg").write_text(svg(sun(660, 110, 60) + tree(110, 560, 180) + grass(570) + lion(420, 330, 1.05)))
# 2 squeak
(OUT/"02-squeak.svg").write_text(svg(lion(300, 340, 1.0, "small") + bubble(470, 60, 290, 150, "squeak", 64) + grass(570)))
# 3 elephant
el = (ellipse(420, 400, 210, 140) + ellipse(230, 250, 90, 120) + ellipse(610, 250, 90, 120)
      + circle(420, 270, 120) + eyes(420, 240, 40)
      + path("M390,320 Q380,430 330,470 Q310,490 340,500 Q420,470 450,320", "#fff")
      + f'<rect x="280" y="480" width="70" height="80" rx="20" fill="#fff" {S}/>'
      + f'<rect x="500" y="480" width="70" height="80" rx="20" fill="#fff" {S}/>')
(OUT/"03-elephant.svg").write_text(svg(el + lion(130, 470, 0.45) + grass(575)))
# 4 monkey in tree
mk = (path("M470,330 Q560,340 540,260 Q520,210 560,200", "none")
      + ellipse(420, 360, 70, 85) + circle(420, 230, 70) + circle(345, 225, 28) + circle(495, 225, 28)
      + ellipse(420, 250, 45, 35) + eyes(420, 215, 22, 8)
      + path("M400,262 Q420,275 440,262"))
(OUT/"04-monkey.svg").write_text(svg(tree(420, 590, 170).replace('y="420"', 'y="420"') + mk + lion(140, 500, 0.4)))
# 5 bird
bd = (ellipse(420, 330, 150, 115) + path("M300,300 Q230,230 250,330 Q260,380 320,360", "#fff")
      + path("M565,310 L650,330 L565,350 Z", "#fff") + circle(500, 300, 12, "#000")
      + path("M360,330 Q420,420 480,330", "#fff")
      + path("M400,440 L390,500 M440,440 L450,500") + path("M150,520 L700,520"))
def note(x, y):
    return ellipse(x, y, 26, 19, "#fff") + path(f"M{x+24},{y} L{x+24},{y-90} Q{x+60},{y-70} {x+64},{y-40}")
notes = note(640, 200) + note(570, 130)
(OUT/"05-bird.svg").write_text(svg(bd + notes))
# 6 ROAR
(OUT/"06-roar.svg").write_text(svg(lion(290, 350, 1.1, "roar") + bubble(440, 40, 340, 170, "ROAR!", 100) + grass(575)))
# 7 friends cheer
cheer = lion(400, 330, 0.8) + "".join(star(x, y, r) for x, y, r in [(90,90,50),(700,110,55),(150,420,40),(660,430,45),(400,70,35)])
for bx, by in [(110, 250), (690, 270)]:
    cheer += ellipse(bx, by, 50, 62) + path(f"M{bx},{by+62} Q{bx+20},{by+120} {bx},{by+170}")
(OUT/"07-cheer.svg").write_text(svg(cheer))
# 8 goodnight
moon = path("M650,70 A110,110 0 1,0 720,260 A90,90 0 1,1 650,70 Z", "#fff")
night = moon + "".join(star(x, y, r) for x, y, r in [(120,90,40),(300,60,30),(470,130,35),(80,260,28)])
night += path("M120,520 Q400,380 700,520 Z", "#fff") + lion(400, 430, 0.55, "small").replace('r="6.1"', 'r="6.1"')
(OUT/"08-goodnight.svg").write_text(svg(night))
print("ok")
