"""Build career_dark.svg / career_light.svg: an animated Career & Education
timeline. A vertical spine draws itself top-to-bottom while each role slides in
with its organisation logo, title and years. Logos are embedded as base64
<image> data URIs (org logos sourced from the web; monogram tile fallback when
no logo is available), so the output is self-contained and theme-aware.

Logos come from tools/career_logos.json:
    { "<key>": {"data_uri": "data:image/png;base64,...", "color": "#rrggbb"},
      "<key>": {"mono": "B", "color": "#rrggbb"} }   # fallback tile

    python3 tools/build_timeline.py
"""
import base64
import json
import os
import re
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGOS_JSON = os.path.join(HERE, "career_logos.json")

# (key, org, role, years) — key "SECTION" marks a section header row.
# Pocket52 and Bobble AI each appear twice (two separate tenures).
TIMELINE = [
    ("SECTION", "Experience", "", ""),
    ("bobble", "Bobble AI", "SVP of Engineering", "2021 — Present"),
    ("gameskraft", "Gameskraft", "Engineering Manager", "2021 — 2021"),
    ("pocket52", "Pocket52", "Lead Architect", "2021 — 2021"),
    ("cloudfeather", "CloudFeather Games", "Co-Founder & CTO", "2020 — 2021"),
    ("pocket52", "Pocket52", "VP of Engineering · Technology Architect", "2018 — 2020"),
    ("bobble", "Bobble AI", "Research & Development Lead", "2015 — 2018"),
    ("sony", "Sony Mobile Communications", "System Verification Engineer", "2014 — 2015"),
    ("srmtech", "SRM Technologies", "Sr. Technical Consultant · Japan", "2013 — 2015"),
    ("nec", "NEC Corporation", "Technical Consultant · Intern · Japan", "2012 — 2014"),
    ("SECTION", "Education", "", ""),
    ("srm_univ", "SRM University", "M.Tech, Computer Science & Engineering · 3rd Rank", "2011 — 2013"),
    ("smit", "Sikkim Manipal Institute of Technology", "B.Tech, Computer Science & Engineering", "2007 — 2011"),
]

# --- geometry ---------------------------------------------------------------
CARD_W = 800
PAD_TOP, PAD_BOTTOM = 60, 24
ROW_H, SEC_H = 56, 40
SPINE_X = 24
TILE_X = 40                       # left edge of the (landscape) logo tile
TILE_W, TILE_H = 88, 46           # logos are mostly wide wordmarks
TILE_CX = TILE_X + TILE_W / 2
LOGO_W, LOGO_H = 74, 30
TEXT_X = 146
YEAR_X = CARD_W - 30
FONT = "font-family=\"'JetBrains Mono','SF Mono',Consolas,Menlo,monospace\""


def theme(mode):
    d = mode == "dark"
    return {
        "bg": "#0d1117" if d else "#ffffff",
        "border": "#30363d" if d else "#d0d7de",
        "spine": "#30363d" if d else "#d0d7de",
        "tile": "#ffffff" if d else "#f6f8fa",
        "tile_border": "#30363d" if d else "#d0d7de",
        "org": "#e6edf3" if d else "#1f2328",
        "role": "#8b949e" if d else "#57606a",
        "year": "#3fb950" if d else "#1a7f37",
        "head": "#58a6ff" if d else "#0969da",
        "dots": "#484f58" if d else "#afb8c1",
        "node": "#58a6ff" if d else "#0969da",
    }


def esc(t):
    import html
    return html.escape(t, quote=True)


def load_logos():
    if os.path.exists(LOGOS_JSON):
        return json.load(open(LOGOS_JSON))
    return {}


def logo_markup(key, org, logos, cy, t):
    """A rounded landscape tile with the org logo (fit inside), or a monogram
    tile fallback. Colours are passed literally — GitHub serves the SVG as an
    image, where CSS var() in presentation attributes does not resolve."""
    info = logos.get(key, {})
    x, y = TILE_X, cy - TILE_H / 2
    color = info.get("color") or "#57606a"
    if info.get("data_uri"):
        lx, ly = TILE_CX - LOGO_W / 2, cy - LOGO_H / 2
        return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{TILE_W}" height="{TILE_H}" rx="10" '
                f'fill="{t["tile"]}" stroke="{t["tile_border"]}"/>'
                f'<image x="{lx:.1f}" y="{ly:.1f}" width="{LOGO_W}" height="{LOGO_H}" '
                f'preserveAspectRatio="xMidYMid meet" href="{info["data_uri"]}"/>')
    mono = info.get("mono") or org[0]
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{TILE_W}" height="{TILE_H}" rx="10" '
            f'fill="{color}"/>'
            f'<text x="{TILE_CX:.1f}" y="{cy + 6:.1f}" text-anchor="middle" '
            f'font-size="18px" font-weight="700" fill="#ffffff">{esc(mono)}</text>')


def build(mode, logos):
    t = theme(mode)
    # y positions
    rows, y = [], PAD_TOP
    for item in TIMELINE:
        h = SEC_H if item[0] == "SECTION" else ROW_H
        rows.append((item, y + h / 2, y))
        y += h
    H = y + PAD_BOTTOM

    entry_cys = [cy for (item, cy, _) in rows if item[0] != "SECTION"]
    spine_top, spine_bot = entry_cys[0], entry_cys[-1]
    spine_len = spine_bot - spine_top

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" width="{CARD_W}" height="{H:.0f}" '
        f'viewBox="0 0 {CARD_W} {H:.0f}" {FONT}>',
        f'<rect x="0.5" y="0.5" width="{CARD_W - 1}" height="{H - 1:.0f}" rx="12" '
        f'fill="{t["bg"]}" stroke="{t["border"]}"/>',
        # title
        f'<text x="30" y="38" font-size="13px" xml:space="preserve">'
        f'<tspan fill="{t["head"]}">- Career &amp; Education </tspan>'
        f'<tspan fill="{t["dots"]}">{"-" * 66}</tspan></text>',
        # spine (draws itself top -> bottom)
        f'<line x1="{SPINE_X}" y1="{spine_top:.1f}" x2="{SPINE_X}" y2="{spine_bot:.1f}" '
        f'stroke="{t["spine"]}" stroke-width="2" stroke-dasharray="{spine_len:.1f}" '
        f'stroke-dashoffset="{spine_len:.1f}">'
        f'<animate attributeName="stroke-dashoffset" from="{spine_len:.1f}" to="0" '
        f'begin="0.2s" dur="1.1s" calcMode="spline" keySplines=".4 0 .2 1" fill="freeze"/>'
        f'</line>',
    ]

    idx = 0
    for (item, cy, top) in rows:
        key = item[0]
        if key == "SECTION":
            out.append(
                f'<text x="30" y="{cy + 4:.1f}" font-size="11px" fill="{t["head"]}" '
                f'letter-spacing="2" opacity="0">{esc(item[1].upper())}'
                f'<animate attributeName="opacity" begin="{0.3 + idx * 0.12:.2f}s" '
                f'dur="0.4s" values="0;1" fill="freeze"/></text>')
            idx += 1
            continue
        _, org, role, years = item
        begin = 0.3 + idx * 0.12
        # node dot on the spine
        node = (f'<circle cx="{SPINE_X}" cy="{cy:.1f}" r="4" fill="{t["node"]}" '
                f'opacity="0"><animate attributeName="opacity" begin="{begin:.2f}s" '
                f'dur="0.3s" values="0;1" fill="freeze"/></circle>')
        # row content slides in from the left
        content = (
            f'<g opacity="0" transform="translate(-14 0)">'
            f'<animate attributeName="opacity" begin="{begin:.2f}s" dur="0.45s" '
            f'values="0;1" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'begin="{begin:.2f}s" dur="0.45s" values="-14 0;0 0" calcMode="spline" '
            f'keySplines=".3 0 .2 1" fill="freeze"/>'
            + logo_markup(key, org, logos, cy, t)
            + f'<text x="{TEXT_X:.0f}" y="{cy - 4:.1f}" font-size="14px" '
              f'font-weight="600" fill="{t["org"]}">{esc(org)}</text>'
            + f'<text x="{TEXT_X:.0f}" y="{cy + 13:.1f}" font-size="11.5px" '
              f'fill="{t["role"]}">{esc(role)}</text>'
            + f'<text x="{YEAR_X:.0f}" y="{cy + 3:.1f}" font-size="12px" '
              f'font-weight="600" text-anchor="end" fill="{t["year"]}">{esc(years)}</text>'
            + '</g>')
        out.append(node + content)
        idx += 1

    out.append('</svg>')
    return "\n".join(out)


if __name__ == "__main__":
    logos = load_logos()
    for mode in ("dark", "light"):
        with open(os.path.join(ROOT, f"career_{mode}.svg"), "w", encoding="utf-8") as f:
            f.write(build(mode, logos))
    have = sum(1 for k in set(i[0] for i in TIMELINE if i[0] != "SECTION")
               if logos.get(k, {}).get("data_uri"))
    print(f"wrote career_dark.svg, career_light.svg  ({have} real logos, "
          f"{len(set(i[0] for i in TIMELINE if i[0] != 'SECTION')) - have} monogram)")
