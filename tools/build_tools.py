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
#
# SECTIONS is a list of (section title, [entries...]); each section gets its own
# dotted header row and its icons flow underneath, COLS per row.
SECTIONS = [
    ("Languages", [
        ("Go", "go", "original"), ("Python", "python", "original"),
        ("C", "c", "original"), ("C++", "cplusplus", "original"),
        ("Rust", "rust", "original"), ("Java", "java", "original"),
        ("TypeScript", "typescript", "original"),
        ("JavaScript", "javascript", "original"), ("Bash", "bash", "original"),
        ("GLSL", "opengl", "plain"),
    ]),
    ("Web &amp; Services", [
        ("Node.js", "nodejs", "original"), ("Next.js", "nextjs", "original"),
        ("Tailwind", "tailwindcss", "original"), ("GraphQL", "graphql", "plain"),
        ("NGINX", "nginx", "original"),
        ("Traefik", "__ic__", "simple-icons/traefikproxy", "#24A1C1"),
    ]),
    ("Data &amp; Streaming", [
        ("PostgreSQL", "postgresql", "original"), ("MySQL", "mysql", "original"),
        ("SQLite", "sqlite", "original"), ("MongoDB", "mongodb", "original"),
        ("Redis", "redis", "original"),
        ("ClickHouse", "__ic__", "simple-icons/clickhouse", "#FAFF69"),
        ("Elasticsearch", "elasticsearch", "original"),
        ("Kafka", "apachekafka", "original"), ("RabbitMQ", "rabbitmq", "original"),
        ("Airflow", "apacheairflow", "original"),
        ("PySpark", "apachespark", "original"),
    ]),
    ("Cloud &amp; Infrastructure", [
        ("GCP", "googlecloud", "original"),
        ("AWS", "amazonwebservices", "original-wordmark"),
        ("Docker", "docker", "original"), ("Podman", "podman", "original"),
        ("Kubernetes", "kubernetes", "original"),
        ("Terraform", "terraform", "original"),
        ("Proxmox", "__ic__", "simple-icons/proxmox", "#E57000"),
        ("ZFS", "__ic__", "simple-icons/openzfs", "#0A2A5E"),
        ("Linux", "linux", "original"),
    ]),
    ("DevOps &amp; Observability", [
        ("Git", "git", "original"), ("GitLab", "gitlab", "original"),
        ("Jenkins", "jenkins", "original"),
        ("Prometheus", "prometheus", "original"),
        ("Grafana", "grafana", "original"), ("Kibana", "kibana", "original"),
        ("Superset", "__ic__", "simple-icons/apachesuperset", "#20A7C9"),
        ("Metabase", "__ic__", "simple-icons/metabase", "#509EE3"),
    ]),
    ("Systems &amp; Embedded", [
        ("Linux Kernel", "linux", "plain"), ("CUDA", "__ic__", "logos/nvidia"),
        ("OpenGL", "opengl", "original"), ("Qt", "qt", "original"),
        ("OpenCV", "opencv", "original"), ("ARM", "__ic__", "logos/arm"),
        ("ESP32", "__ic__", "simple-icons/espressif", "#E7352C"),
        ("Arduino", "arduino", "original"), ("Android", "android", "original"),
        ("Android NDK", "android", "plain"),
    ]),
]

TOOLS = [e for _, entries in SECTIONS for e in entries]

COLS = 7
PULSE_DUR = 9.0                  # header "packet" loop, seconds
SWEEP_DUR = 14.0                 # tile self-test sweep loop, seconds
CELL_W, CELL_H = 128, 104
PAD_X, PAD_TOP = 26, 56
SEC_H = 40                       # vertical space taken by a section header row
TILE = 60
ICON = 38
LABEL_DY = 21


UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as r:
        return r.read().decode("utf-8")


SI_COLOR = {}                                    # brand colour for monochrome simple-icons


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


def rule(x, y, title, head, dots, width_px, fs=13, pulse=None, delay=0.0):
    """`- Title ------------` header line, dashes padded to width_px.

    With `pulse` (a colour) a short bright segment rides the dashes left to
    right on a slow loop — the dotted rule read as a bus, one packet on it."""
    label = f"- {title} "
    plain = len(re.sub(r"&[a-z]+;", "x", label))          # entities are 1 glyph
    fill = max(int(width_px / (fs * 0.6)) - plain, 3)
    out = (f'<text x="{x}" y="{y}" font-size="{fs}px" xml:space="preserve">'
           f'<tspan fill="{head}">{label}</tspan>'
           f'<tspan fill="{dots}">{"-" * fill}</tspan></text>')
    if not pulse:
        return out
    x0 = x + plain * fs * 0.6
    travel = fill * fs * 0.6 - 14
    out += (f'<rect x="{x0:.1f}" y="{y - 4:.1f}" width="14" height="1.6" rx="0.8" '
            f'fill="{pulse}" opacity="0">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'dur="{PULSE_DUR}s" begin="{delay:.2f}s" repeatCount="indefinite" '
            f'values="0 0;{travel:.0f} 0" calcMode="spline" keySplines=".45 0 .55 1"/>'
            f'<animate attributeName="opacity" dur="{PULSE_DUR}s" begin="{delay:.2f}s" '
            f'repeatCount="indefinite" values="0;0.85;0.85;0;0" '
            f'keyTimes="0;0.08;0.72;0.85;1"/></rect>')
    return out


def build(mode, icons):
    dark = mode == "dark"
    bg = "#0d1117" if dark else "#ffffff"
    border = "#30363d" if dark else "#d0d7de"
    tile = "#ffffff" if dark else "#f6f8fa"
    tile_border = "#30363d" if dark else "#d0d7de"
    label = "#c9d1d9" if dark else "#24292f"
    head = "#58a6ff" if dark else "#0969da"
    dots = "#484f58" if dark else "#afb8c1"
    green = "#3fb950" if dark else "#1a7f37"

    W = PAD_X * 2 + COLS * CELL_W
    inner_w = W - 2 * PAD_X
    H = PAD_TOP + sum(SEC_H + ((len(e) + COLS - 1) // COLS) * CELL_H
                      for _, e in SECTIONS) + 12
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" '
        f'font-family="\'JetBrains Mono\',\'SF Mono\',Consolas,Menlo,monospace">',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" '
        f'fill="{bg}" stroke="{border}"/>',
        rule(PAD_X, 36, "Tech &amp; Tools", head, dots, inner_w,
             pulse=green, delay=0.0),
        # terminal cursor parked after the title
        f'<rect x="{PAD_X + 15 * 7.8:.0f}" y="26" width="7" height="12" fill="{green}">'
        f'<animate attributeName="opacity" dur="1.1s" repeatCount="indefinite" '
        f'values="1;1;0;0" keyTimes="0;0.5;0.52;1"/></rect>',
    ]
    i, y = 0, PAD_TOP
    for si, (title, entries) in enumerate(SECTIONS):
        out.append(rule(PAD_X, y + 20, title, head, dots, inner_w, fs=12,
                        pulse=green, delay=1.1 + si * 1.35))
        y += SEC_H
        for j, entry in enumerate(entries):
            vb, inner = icons[i + j]
            col, row = j % COLS, j // COLS
            cx = PAD_X + col * CELL_W + CELL_W / 2
            cy = y + row * CELL_H + TILE / 2
            # tiles light up in a diagonal sweep, like a slow POST self-test
            sweep = SWEEP_DUR * 0.02 * (col + row + si * 2)
            out.append(
                f'<rect x="{cx - TILE / 2:.1f}" y="{cy - TILE / 2:.1f}" width="{TILE}" '
                f'height="{TILE}" rx="14" fill="{tile}" stroke="{tile_border}">'
                f'<animate attributeName="stroke" dur="{SWEEP_DUR}s" '
                f'begin="{sweep:.2f}s" repeatCount="indefinite" '
                f'values="{tile_border};{green};{tile_border};{tile_border}" '
                f'keyTimes="0;0.02;0.06;1"/></rect>')
            out.append(icon_group(vb, inner, cx, cy, ICON))
            out.append(
                f'<text x="{cx:.1f}" y="{cy + TILE / 2 + LABEL_DY:.1f}" fill="{label}" '
                f'font-size="12px" text-anchor="middle">{entry[0]}</text>')
        y += ((len(entries) + COLS - 1) // COLS) * CELL_H
        i += len(entries)
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
