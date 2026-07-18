"""Regenerate tools/career_logos.json from the logo files in tools/logos/.

Keeps the timeline reproducible offline: the raw org/university logos are
committed under tools/logos/, and this script base64-embeds them into
career_logos.json (which build_timeline.py reads). No network, no image
libraries — just base64. Colours + monogram fallbacks live in tools/logos/meta.json.

    python3 tools/bake_logos.py
"""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO_DIR = os.path.join(HERE, "logos")
META = os.path.join(LOGO_DIR, "meta.json")
OUT = os.path.join(HERE, "career_logos.json")


def bake():
    meta = json.load(open(META)) if os.path.exists(META) else {"colors": {}, "mono": {}}
    colors, mono = meta.get("colors", {}), meta.get("mono", {})
    out = {}
    for fn in sorted(os.listdir(LOGO_DIR)):
        if not fn.endswith(".png"):
            continue
        key = fn[:-4]
        b64 = base64.b64encode(open(os.path.join(LOGO_DIR, fn), "rb").read()).decode()
        out[key] = {"data_uri": f"data:image/png;base64,{b64}",
                    "color": colors.get(key, "#57606a")}
    # monogram-only entries (no logo file)
    for key, m in mono.items():
        if key not in out:
            out[key] = {"mono": m, "color": colors.get(key, "#57606a")}
    json.dump(out, open(OUT, "w"))
    total = sum(len(v.get("data_uri", "")) for v in out.values()) // 1024
    print(f"wrote career_logos.json — {len(out)} logos, {total} KB embedded")


if __name__ == "__main__":
    bake()
