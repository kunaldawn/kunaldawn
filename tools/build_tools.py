"""Build tools_dark.svg / tools_light.svg: a labelled grid of tech icons.

Icons are inlined from Devicon (colour "original" variants where available) so
the output is self-contained and renders on GitHub as an image. Every icon sits
on a light rounded tile so dark logos (rust, bash, aws) stay visible on both
themes; the label under each icon is themed. Re-run to refresh icons:

    python3 tools/build_tools.py

Writes tools_dark.svg and tools_light.svg in the repo root.
"""
import os
import re
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEVICON = "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/{n}/{n}-{v}.svg"

# Each entry: (label, source, ref[, color])
#   devicon:      (label, "<devicon-name>", "<variant>")
#   simple-icons: (label, "__si__", "<slug>")                 tinted via SI_COLOR
#   iconify:      (label, "__ic__", "<prefix>/<name>"[, "#hex"])  hex tints mono sets
TOOLS = [
    # languages
    ("Go", "go", "original"), ("Python", "python", "original"),
    ("C", "c", "original"), ("C++", "cplusplus", "original"),
    ("Rust", "rust", "original"), ("Java", "java", "original"),
    ("TypeScript", "typescript", "original"),
    ("JavaScript", "javascript", "original"), ("Bash", "bash", "original"),
    ("Node.js", "nodejs", "original"), ("Next.js", "nextjs", "original"),
    ("Tailwind", "tailwindcss", "original"), ("Angular", "angular", "original"),
    ("D3.js", "d3js", "original"),
    # backend / messaging
    ("Docker", "docker", "original"), ("Podman", "podman", "original"),
    ("Kubernetes", "kubernetes", "original"), ("NGINX", "nginx", "original"),
    ("Kafka", "apachekafka", "original"), ("RabbitMQ", "rabbitmq", "original"),
    ("GraphQL", "graphql", "plain"),
    # data
    ("PostgreSQL", "postgresql", "original"), ("MongoDB", "mongodb", "original"),
    ("Redis", "redis", "original"), ("SQLite", "sqlite", "original"),
    ("MySQL", "mysql", "original"), ("CockroachDB", "__si__", "cockroachlabs"),
    ("Elasticsearch", "elasticsearch", "original"),
    ("Airflow", "apacheairflow", "original"), ("PySpark", "apachespark", "original"),
    # analytics / observability / cloud
    ("Superset", "__ic__", "simple-icons/apachesuperset", "#20A7C9"),
    ("Metabase", "__ic__", "simple-icons/metabase", "#509EE3"),
    ("Grafana", "grafana", "original"), ("Kibana", "kibana", "original"),
    ("GCP", "googlecloud", "original"), ("AWS", "amazonwebservices", "original-wordmark"),
    ("Git", "git", "original"),
    # devops / compute
    ("GitLab", "gitlab", "original"), ("Jenkins", "jenkins", "original"),
    ("CircleCI", "circleci", "plain"), ("CUDA", "__ic__", "logos/nvidia"),
    ("OpenGL", "opengl", "original"), ("Linux", "linux", "original"),
    ("Linux Kernel", "linux", "plain"),
    # hardware / platforms
    ("ARM", "__ic__", "logos/arm"),
    ("ESP32", "__ic__", "simple-icons/espressif", "#E7352C"),
    ("Android", "android", "original"), ("Arduino", "arduino", "original"),
    ("OpenCV", "opencv", "original"), ("Qt", "qt", "original"),
]

COLS = 7
CELL_W, CELL_H = 128, 104
PAD_X, PAD_TOP = 26, 56
TILE = 60
ICON = 38
LABEL_DY = 21


UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as r:
        return r.read().decode("utf-8")


SI_COLOR = {"cockroachlabs": "#6933FF"}          # brand colour for monochrome simple-icons


def namespace_ids(svg, uid):
    """Prefix every internal id (and its url(#)/href references) so gradients and
    clipPaths from different icons never collide when inlined into one document."""
    for x in set(re.findall(r'\bid="([^"]+)"', svg)):
        nx = f"{uid}{x}"
        svg = svg.replace(f'id="{x}"', f'id="{nx}"')
        svg = svg.replace(f'url(#{x})', f'url(#{nx})')
        svg = svg.replace(f'href="#{x}"', f'href="#{nx}"')
    return svg


def load_icon(name, variant, color=None, uid=""):
    if name == "__si__":
        # simple-icons raw SVGs are single-path monochrome; tint with brand colour
        svg = fetch(f"https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{variant}.svg")
        col = color or SI_COLOR.get(variant, "#57606a")
        svg = svg.replace("<path", f'<path fill="{col}"', 1)
    elif name == "__ic__":
        # iconify: "prefix/name"; colour param tints monochrome sets (simple-icons, mdi)
        url = f"https://api.iconify.design/{variant}.svg"
        if color:
            url += f"?color=%23{color.lstrip('#')}"
        svg = fetch(url)
    else:
        svg = fetch(DEVICON.format(n=name, v=variant))
    m = re.search(r'viewBox="([^"]+)"', svg)
    if m:
        vb = [float(x) for x in m.group(1).split()]
    else:
        w = re.search(r'width="([\d.]+)"', svg)
        h = re.search(r'height="([\d.]+)"', svg)
        vb = [0, 0, float(w.group(1)) if w else 128, float(h.group(1)) if h else 128]
    inner = re.sub(r'^.*?<svg[^>]*>', '', svg, count=1, flags=re.S)
    inner = re.sub(r'</svg>\s*$', '', inner, flags=re.S).strip()
    inner = re.sub(r'<\?xml.*?\?>', '', inner, flags=re.S)
    if uid:
        inner = namespace_ids(inner, uid)
    return vb, inner


def icon_group(vb, inner, cx, cy, box):
    vw, vh = vb[2], vb[3]
    s = box / max(vw, vh)
    tx = cx - (vb[0] + vw / 2) * s
    ty = cy - (vb[1] + vh / 2) * s
    return f'<g transform="translate({tx:.2f} {ty:.2f}) scale({s:.4f})">{inner}</g>'


def build(mode, icons):
    dark = mode == "dark"
    bg = "#0d1117" if dark else "#ffffff"
    border = "#30363d" if dark else "#d0d7de"
    tile = "#ffffff" if dark else "#f6f8fa"
    tile_border = "#30363d" if dark else "#d0d7de"
    label = "#c9d1d9" if dark else "#24292f"
    head = "#58a6ff" if dark else "#0969da"
    dots = "#484f58" if dark else "#afb8c1"

    rows = (len(TOOLS) + COLS - 1) // COLS
    W = PAD_X * 2 + COLS * CELL_W
    H = PAD_TOP + rows * CELL_H + 20
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" '
        f'font-family="\'JetBrains Mono\',\'SF Mono\',Consolas,Menlo,monospace">',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" '
        f'fill="{bg}" stroke="{border}"/>',
        f'<text x="{PAD_X}" y="36" font-size="13px" xml:space="preserve">'
        f'<tspan fill="{head}">- Tech &amp; Tools </tspan>'
        f'<tspan fill="{dots}">{"-" * 78}</tspan></text>',
    ]
    n = len(TOOLS)
    for i, entry in enumerate(TOOLS):
        lbl = entry[0]
        vb, inner = icons[i]
        col, row = i % COLS, i // COLS
        in_row = min(COLS, n - row * COLS)          # centre a short final row
        row_off = (COLS - in_row) * CELL_W / 2
        cx = PAD_X + row_off + col * CELL_W + CELL_W / 2
        cy = PAD_TOP + row * CELL_H + TILE / 2
        out.append(
            f'<rect x="{cx - TILE / 2:.1f}" y="{cy - TILE / 2:.1f}" width="{TILE}" '
            f'height="{TILE}" rx="14" fill="{tile}" stroke="{tile_border}"/>')
        out.append(icon_group(vb, inner, cx, cy, ICON))
        out.append(
            f'<text x="{cx:.1f}" y="{cy + TILE / 2 + LABEL_DY:.1f}" fill="{label}" '
            f'font-size="12px" text-anchor="middle">{lbl}</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    icons = []
    for entry in TOOLS:
        lbl, name, variant = entry[0], entry[1], entry[2]
        color = entry[3] if len(entry) > 3 else None
        try:
            icons.append(load_icon(name, variant, color, uid=f"i{len(icons)}_"))
            print("ok  ", lbl)
        except Exception as e:
            print("FAIL", lbl, name, variant, e)
            icons.append(([0, 0, 24, 24], ""))
    for mode in ("dark", "light"):
        with open(os.path.join(ROOT, f"tools_{mode}.svg"), "w", encoding="utf-8") as f:
            f.write(build(mode, icons))
    print("wrote tools_dark.svg, tools_light.svg")
