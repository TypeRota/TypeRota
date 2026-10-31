
#!/usr/bin/env python3
"""生成 assets/banner-{dark,light}.svg 和 assets/divider.svg。

只在本地跑一次：标题依赖系统字体，需要 fontTools 把文字转成 path。
CI 上不跑这个脚本，只用 tools/render.py 生成统计卡。

    python3 tools/gen_assets.py
"""
import base64, math, pathlib, random, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import svgtext as st

W, H = 1200, 360
SERIF = st.load("/usr/share/fonts/noto-cjk/NotoSerifCJK-Light.ttc", 2)
MED   = st.load("/usr/share/fonts/noto-cjk/NotoSerifCJK-Medium.ttc", 2)
BEBAS = st.load("/usr/local/share/fonts/b/BebasNeue_Regular.ttf", 0)
MONO  = st.load("/usr/share/fonts/maple/MapleMono-NF-CN-Regular.ttf", 0)
SANS  = st.load("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc", 2)

ROOT = HERE.parent
AVATAR = base64.b64encode((ROOT / "assets/avatar.png").read_bytes()).decode()

def stars(rnd, n):
    out = []
    for _ in range(n):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        r = rnd.choice([0.6, 0.7, 0.8, 1.0, 1.3, 1.7])
        o = round(rnd.uniform(0.18, 0.92), 2)
        col = rnd.choices(["#EDEFF7", "#BFD7FF", "#EFC77E", "#A78BFA"], [70, 14, 10, 6])[0]
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{col}" opacity="{o}"/>')
    return "".join(out)

def orbit(cx, cy, rx, ry, rot, color):
    s = f'<g transform="rotate({rot} {cx} {cy})">'
    s += (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="{color}" '
          f'stroke-opacity="0.40" stroke-width="1.1" stroke-dasharray="3 7"/>')
    for a in (18, 132, 250):
        x = cx + rx * math.cos(math.radians(a))
        y = cy + ry * math.sin(math.radians(a))
        s += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#EFC77E" opacity="0.9"/>'
        s += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#EFC77E" opacity="0.13"/>'
    return s + "</g>"

def render(theme):
    dark = theme == "dark"
    if dark:
        c = dict(sky0="#05070F", sky1="#0B1024", sky2="#1A1433", haze="#7C6BD6",
                 text="#EDEFF7", muted="#8B93B8", accent="#A78BFA", gold="#EFC77E", orb="#4B3F86",
                 ring="#B79BE8", halo="#7C6BD6")
    else:
        c = dict(sky0="#FBFAFE", sky1="#F2EFFA", sky2="#E6E1F4", haze="#B9A8EE",
                 text="#241A3E", muted="#6F6790", accent="#7C5BD6", gold="#C99A3E", orb="#C9BEE8",
                 ring="#8A6BD0", halo="#B9A8EE")
    rnd = random.Random(20261031)
    star_el = stars(rnd, 320) if dark else stars(rnd, 160)

    orbits = "".join(
        f'<path d="M{180 + i * 30} {H} A {520 + i * 70} {520 + i * 70} 0 0 1 {W - 40 - i * 18} {H}" '
        f'fill="none" stroke="{c["orb"]}" stroke-opacity="{0.28 - i * 0.05:.2f}" stroke-width="1"/>'
        for i in range(4))

    ring = orbit(958, 148, 152, 62, -16, c["accent"])

    word, _ = st.text_path(MED, "萝塔", 106, 80, 186, tracking=2)
    latin, _ = st.text_path(BEBAS, "TYPEROTA", 40, 82, 246, tracking=12)
    tag, _ = st.text_path(MONO, "SUPERAGENTS", 15, 84, 284, tracking=4)
    gov, _ = st.text_path(SANS, "受 LaT-SKY 管辖", 14, 84, 316, tracking=0.5)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="萝塔 / TypeRota">
<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{c["sky0"]}"/><stop offset="0.55" stop-color="{c["sky1"]}"/><stop offset="1" stop-color="{c["sky2"]}"/></linearGradient>
<radialGradient id="haze" cx="0.5" cy="0.5" r="0.5">
<stop offset="0" stop-color="{c["haze"]}" stop-opacity="0.30"/><stop offset="1" stop-color="{c["haze"]}" stop-opacity="0"/></radialGradient>
<radialGradient id="halo" cx="0.5" cy="0.5" r="0.5">
<stop offset="0.60" stop-color="{c["halo"]}" stop-opacity="0.00"/>
<stop offset="0.82" stop-color="{c["halo"]}" stop-opacity="0.22"/>
<stop offset="1" stop-color="{c["halo"]}" stop-opacity="0"/></radialGradient>
<clipPath id="round"><rect x="0" y="0" width="{W}" height="{H}" rx="16"/></clipPath>
</defs>
<g clip-path="url(#round)">
<rect width="{W}" height="{H}" fill="url(#sky)"/>
<ellipse cx="880" cy="330" rx="520" ry="260" fill="url(#haze)"/>
{orbits}
{star_el}
{ring}
<circle cx="958" cy="148" r="132" fill="url(#halo)"/>
<image x="872" y="62" width="172" height="172" xlink:href="data:image/png;base64,{AVATAR}"/>
<circle cx="958" cy="148" r="88" fill="none" stroke="{c["ring"]}" stroke-opacity="0.55" stroke-width="1.4"/>
<path d="{word}" fill="{c["text"]}"/>
<path d="{latin}" fill="{c["accent"]}"/>
<path d="{tag}" fill="{c["muted"]}"/>
<rect x="84" y="296" width="228" height="1" fill="{c["gold"]}" opacity="0.55"/>
<path d="{gov}" fill="{c["gold"]}" opacity="0.85"/>
</g>
</svg>'''

outdir = ROOT / "assets"
for th in ("dark", "light"):
    (outdir / f"banner-{th}.svg").write_text(render(th))
print("written")

def divider():
    """分隔线：一条渐隐的轨道 + 中央一颗四芒星。"""
    d = ('M0 13L470 13L492 10L512 16L534 7L556 15L574 13L626 13'
         'L644 11L666 18L688 8L708 16L730 13L1200 13')
    star = ('M600 4C601.9 11.1 601.9 11.1 609 13C601.9 14.9 601.9 14.9 600 22'
            'C598.1 14.9 598.1 14.9 591 13C598.1 11.1 598.1 11.1 600 4Z')
    inner = ('M600 9C600.8 12.2 600.8 12.2 604 13C600.8 13.8 600.8 13.8 600 17'
             'C599.2 13.8 599.2 13.8 596 13C599.2 12.2 599.2 12.2 600 9Z')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="26" viewBox="0 0 {W} 26" role="img" aria-label="分隔线">
<defs>
<linearGradient id="dl" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="#A78BFA" stop-opacity="0"/>
<stop offset="0.30" stop-color="#A78BFA" stop-opacity="0.32"/>
<stop offset="0.46" stop-color="#A78BFA" stop-opacity="0.60"/>
<stop offset="0.54" stop-color="#A78BFA" stop-opacity="0.60"/>
<stop offset="0.70" stop-color="#A78BFA" stop-opacity="0.32"/>
<stop offset="1" stop-color="#A78BFA" stop-opacity="0"/>
</linearGradient>
</defs>
<path d="{d}" fill="none" stroke="url(#dl)" stroke-width="1.6" stroke-linecap="round"/>
<path d="{star}" fill="#EFC77E" opacity="0.95"/>
<path d="{inner}" fill="#FFFFFF" opacity="0.92"/>
</svg>'''


if __name__ == "__main__":
    outdir = ROOT / "assets"
    outdir.mkdir(exist_ok=True)
    for th in ("dark", "light"):
        (outdir / f"banner-{th}.svg").write_text(render(th))
    (outdir / "divider.svg").write_text(divider())
    print("assets/banner-{dark,light}.svg · assets/divider.svg")
