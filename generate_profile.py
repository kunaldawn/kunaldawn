"""Regenerate dark_mode.svg / light_mode.svg for the GitHub profile.

A neofetch-style card. On the left, a column of green "Matrix" glyphs rains down
and crystallises into a high-resolution, per-glyph grayscale portrait — each
column forms top-to-bottom behind the falling rain, holds, then melts back into
rain and loops. On the right, a key/value info panel with live GitHub stats.
Runs daily via GitHub Actions. Standard library only — the portrait is pre-baked
below, so CI needs no image libraries.

Design inspired by github.com/DietrichGebert/DietrichGebert (ASCII portrait +
neofetch panel). The grayscale-glyph face and the Matrix crystallise animation
are original.
"""
import html
import json
import os
import random
import urllib.request
from datetime import datetime, timezone

USER = "kunaldawn"
JOINED_YEAR = 2013            # GitHub account creation year, never changes
SEED = 7                      # deterministic rain -> small, stable diffs

# ---------------------------------------------------------------------------
# Pre-baked grayscale portrait. Each row is (glyphs, levels): one char per cell
# and a matching brightness bucket '0'..'P' (0..25). Baked offline from the
# headshot (background matte + local-contrast luminance ramp). Regenerate with
# tools/bake_face.py if the photo changes.
# ---------------------------------------------------------------------------
LVL = "0123456789ABCDEFGHIJKLMNOP"      # 26 brightness buckets

FACE = [
    ('                                MbaM=   `: :', '00000000000000000000000000000000PKLP60002303'),
    ('                             MMMMMMMhX4Wa#hMMMMMMW', '00000000000000000000000000000PPPPPPPKFINMNLOPPPPPO'),
    ('                       MMMMMMMMJC0uCaM#MMM%%MM%@MMMMM', '00000000000000000000000PPPPPPPPCDHBDLPNPPPMNPPNOPPPPP'),
    ('                   MMMMMMMMM%t=nJdWpXxtOd0Y%MM#MMMMMMMMMM', '0000000000000000000PPPPPPPPPN96BDJNKFA9GJHDNPPNPPPPPPPPPP'),
    ('                aMMMMMMMM#z u0paMM#MMMMMM@Q%MMMMMp+MMMMMMMMM', '0000000000000000LPPPPPPPPNA1BGKLPPNPPPPPPOHMPPPPPK6PPPPPPPPP'),
    ('               MMMM%MMdhnz   iXdbhbaakJv,   z^ laMwMMMMM0MMMMh', '000000000000000PPPPNPPJLBA0007FJJLKLLIC94000A507LPMPPPPPHPPPPL'),
    ('              MMMp4XCJui`d    _+^      .=Ckh%4v_~i^tMMM@%MMMMMM', '00000000000000PPPKIFDCB71J000036510000015DILMI834759PPPOMPPPPPP'),
    ('             MMxzzUc   4pu                 ^ctY0k40QnoZuaYMMMMM#@', '0000000000000PP9AAE8000IKB00000000000000000589DHIIHHACGBLDPPPPPNO'),
    ('            MM+,zzzCuQUO                         +   c0dYhMMMMaUbQ', '000000000000PP64AAADBHEG000000000000000000000000060008HJELPPPPLEKH'),
    ('            Mz Xw+``zMMh                                    abMMMMW', '000000000000PA0FM611APPL000000000000000000000000000000000000LKPPPPN'),
    ('           MM vQp  n@4XZ      ,`                    ,^      vun%#MMb', '00000000000PP09HK00BOIFF0000004200000000000000000000450000009BBNNPPK'),
    ('           M@:x0  MMMOxnUi`-~=xb%0XUcl=~               cc,=icv+zQJMWh', '00000000000PO3AH00PPPG9BE722569KNGFE876500000000000000088457886AHDPOL'),
    ('           MMUnZ `kMM@hXZY+^++i+,cvxU@MMMMMMMpov-        _izoxvCMMMMMM', '00000000000PPEBF02IPPOLFGD6566664899EOPPPPPPPKC820000000037AC98DPPPPPP'),
    ('           MM ,0 `Ybc-ili+^-`       0MMMMMMMMMhOuc=          `+Cw4#MMM', '00000000000PP04G01EK8277765210000000HPPPPPPPPOLGB86000000000016DMINPPP'),
    ('           Mx  `c +v^     . -:~-,:`XMMMMMMMMMMM#4UYc:             `zMM#', '00000000000PA0018068500000102352432FPPPPPPPPPPPNIED8300000000000001APPN'),
    ('           Mo      ~      :il=-,odMMMMMMMMMMMMMMMMMMMho_          `+x@@', '00000000000PC0000005000000377624CJPPPPPPPPPPPPPPPPPPPLC3000000000016AOO'),
    ('           Mo,            ,-+zUaMMMMMMMMMMMMMMMMMMMMMMMMMMk      ` ~W@', '00000000000PC4000001000000426AELPPPPPPPPPPPPPPPPPPPPPPPPPPI000000105NO'),
    ('           M^           =+~YMMMMMMMMMM##MMMMMMMMMMMMMMMMMMMM4       4%', '00000000000P500000000000664EPPPPPPPPPPNNPPPPPPPPPPPPPPPPPPPPI0000000IN'),
    ('                        Otx@k`:xn         :zCJu:       ^YkdWM0      bM', '000000000000000000000000G9AOI239B0000000003ADCB200000005EIJNPH000000KP'),
    ('            _          nkUl, iZ@MMMo       kMMk      iMMMMMMaWU     #M', '00000000000030000000000BIE7407GOPPPC0000001IPPI0000007PPPPPPMNE00000NP'),
    ('            x          #WY-~c_.           CMMMM+           vpJM     M', '00000000000090000000000NOD2583100000000000DPPPP6000000000009KDP00000P'),
    ('            U  c:     ~MMOi         U    zdMMMMw    .        hM     MM', '000000000000E0082000005PPG6000000000E0000AJPPPPM0000100000000KP00000PP'),
    ('             Zk^+oX:  #MMMpxuv-=JCQ0YkMMaM@pMMMMaawo^cCU0UdMWMMu   MM', '0000000000000FI56CF300NPPPK9B826DDHGDIPPLPOKPPPPLLMC58DEHEJPNPPB000PP'),
    ('            MM4       MMMMMMMMbnl~^t%MMM@#QMMMMMMMMMMC`  cwMMMMM   MMM', '000000000000PPI0000000PPPPPPPPKB7559NPPPONHPPPPPPPPPPD1008MPPPPP000PPP'),
    ('           MMJx      tMMMMMMMMMMMMMMMMMMMMdMMMMMMMMMMMMMMMMMMMMM   nMM', '00000000000PPDA0000009PPPPPPPPPPPPPPPPPPPPJPPPPPPPPPPPPPPPPPPPPP000APP'),
    ('           MWwMM     tMMMMMMMMMMMMMMMUtMMMMMMMMMMMMM,MMMMMMMMMMM  MMMM', '00000000000POMPP000009PPPPPPPPPPPPPPPE9PPPPPPPPPPPPP4PPPPPPPPPPP00PPPP'),
    ('           MMMMMa     kdMMMMMMMMMMMY       `nJJZc. ~  v@MMMMMMMM  MMM@', '00000000000PPPPPL00000IJPPPPPPPPPPPE00000001BCCG8105009OPPPPPPPP00PPPO'),
    ('           MMMMM^  M  x4hpOYphhh0X_  ^C            0z  _U4haW@Md iMMM', '00000000000PPPPP500P00AILKGEKLKLHF3005D000000000000GA003EILLNOPJ07PPP'),
    ('            WMMMv t%#oZh0o^=nnx+-   UWMMMhz     OMMMMn  `ioJzJ%k XMM', '000000000000NPPP909NNCFLHC56BBA62000EOPPPLA00000GPPPPB0017CDADMI0FPP'),
    ('             MMMMC%4QO4@kvxi_: `   ohMMMMWpXt^lXpWMMMM+  ^itcz4%MMMb', '0000000000000PPPPDMIHGIOI9A73301000CLPPPPOKF957FKOPPPP6005798AIMPPPK'),
    ('              MMMMMMdt0whol__:-=u .                  XU vCtnxnaMMMM', '00000000000000PPPPPPJ9HMLC733326B01000000000000000000FE09D9B9BLPPPP'),
    ('               MMMMMMM4hhkU+lno0Ma:-    ~uo =-Mp0~   XQQMwYtckMMMMM', '000000000000000PPPPPPPILLIE67BCHPL2200004BC062PKG4000FHHPME98IPPPPP'),
    ('                MMMMM~ dpQXollUbMMUMMM#WMMMMMMMMMMMMMMhbM4JJ0WnxMMM', '0000000000000000PPPPP50JKHFC77EJPPEPPPNNPPPPPPPPPPPPPPKJPIDCHNBAPPP'),
    ('                        @UnnCuiu4%@MMMu_   ixl:   i#MMMbUvoQ%M', '000000000000000000000000OEBBDB7BIMOPPPB30006A720006NPPPKE8CHMP'),
    ('                        xQxxzun=+QMMMMMz        .tpMMMMwunoZMM', '0000000000000000000000009HAAABB56HPPPPPA0000000019KPPPPMBACFPP'),
    ('                         0t+ltxx~idMMMMMMMMMMMMMMMMMMMM0ooY%M', '0000000000000000000000000H96799A57JPPPPPPPPPPPPPPPPPPPPHCCDMP'),
    ('                        +a~`-:itx=,xkMMMMMMMMMMMMMMMM%CcnlCpY', '0000000000000000000000006L412369954AIPPPPPPPPPPPPPPPPND8B7DKE'),
    ('                        OMl   ._~~.  =coQMMMMWhdbkv^=  +,_v+', '000000000000000000000000GP7000135510058CHPPPPNLJKI9550064386'),
    ('                        oMb^      .                    ``ov', '000000000000000000000000CPK500000010000000000000000000011C8'),
    ('                       %nMM4t:                       `  zM', '00000000000000000000000MAPPI9300000000000000000000000100AP'),
    ('                     aMM^MMMdo^                       .tMM', '000000000000000000000LPP5PPPJC50000000000000000000000019PP'),
    ('                    pM@d`MMMMbJt^,^`                 -zMMM', '00000000000000000000KPOJ2PPPPKC95451000000000000000002APPP'),
    ('                   MMMZZ xMM@%dOooZXuzc~:`.    _^inuzUWMMM#', '0000000000000000000PPPFG0APPOMJGCCFFBA852210000357BBAEOPPPN'),
    ('                  MM%wol  bMMMMpQUU0kkO0ZXXUZOOhhbbbwMMMM nMM', '000000000000000000PPMMC700KPPPPKHEEHIIGHFFFEFGGLLKKKMPPPP0BPP'),
    ('                 @M%=i:,.  MMMMW#dXQahkQkp#MMMMM#dbaMMMMM _MMM', '00000000000000000OPM5624100PPPPONJFHLLIHIKNPPPPPNJKMPPPPP03PPP'),
    ('                ZMM4z~-    MMMM@MMhQhpQQOOQpMM@dXQkhMMMMM tMMMM', '0000000000000000FPPIA520000PPPPOPPLHLKHHGGHKPPOJFHILPPPPP09PPPP'),
    ('               QnZpzzC,    .MMMMMWbZZZXXYJc_:~+nYZk%MMMMi  MMMMM', '000000000000000HAFKAAD400001PPPPPOKGFFFFDD83356BEFINPPPP700PPPPP'),
    ('             MMMUXv-.CC .   4MMMMMWOzuoUYJc    =nUZwMMMW   0MMMMM', '0000000000000PPOEF821DD01000IPPPPPNGABCEED810005AEFMPPPN000HPPPPP'),
    ('          tMMMMw44c+c^~_tznn^vY%MMWkZQbhOCnzCCCouXhMM#hu      :UMM', '00000000009PPPPMII8685539ABB59ENPPNIGHKKGDBADDDCBFKPPNKB0000002EPP'),
    ('   UpCoc UMMMUZk4uinJ4zZw%%Zt^ `oWMdZZ0dd4QhMM@hd#MwkQ0c       JWMMM', '000EKDC80EPPPEFIIB7BDIAFMMNF9501CNPJFFHJJIHLPPOLJNPMIHH80000000COPPP'),
    ('buY#MM%nWMkMMC=vXnl^iCOwOYo_toi:,c4bXovllvCCuYUZha4OXYZ~     pwt  MMMMWMMMMM', 'KBENPPNBNPIPPD69FB757DGMGDC39C7348IKFC8778DDBDEGLMIGFEG500000KM900PPPPNPPPPP'),
    ('MWMMMMuMMW~Cd0Coou:~lcnz  ~_UkoZv  ZXkXCntcivYZbhp0JY0Xi    pM#    MMMYnMMMMMMMMMMMMM', 'PNPPPPBPPN5DJGDCCB3478BA0043EICF800FFIFDA9879EFJLKGDDHF70000KPN0000PPPDBPPPPPPPPPPPPP'),
]

# ---------------------------------------------------------------------------
# Info panel content. Everything here is public or derivable from the profile.
# ---------------------------------------------------------------------------
INFO = {
    "handle": f"{USER}@github",
    "role": "SVP of Engineering",
    "company": "Bobble AI",
    "location": "Bangalore, India",
    "focus": "Backend / Distributed Systems / Agentic AI",
    "languages": "Go / Python / C / C++ / Rust",
    "infra": "GCP / AWS / On-Prem",
    "editor": "Claude Code / VS Code",
    "hobbies": "Homebrew Electronics",
    "archival": "Homebrew Digital @ kunaldawn.com",
    "linkedin": "in/kunal-dawn",
    "youtube": "c/kunaldawn",
    "github": f"@{USER}",
}

PALETTES = {
    "dark": {
        "light": False,
        "bg": "#0d1117", "border": "#30363d",
        "h": "#58a6ff", "k": "#ffa657", "v": "#c9d1d9", "d": "#484f58",
        "g": "#3fb950", "r": "#f85149",
        "rain": "#2ea043", "rain_head": "#c5f7cd",
    },
    "light": {
        "light": True,
        "bg": "#ffffff", "border": "#d0d7de",
        "h": "#0969da", "k": "#953800", "v": "#24292f", "d": "#afb8c1",
        "g": "#1a7f37", "r": "#cf222e",
        "rain": "#1a7f37", "rain_head": "#0a3d1a",
    },
}

# --- geometry ---------------------------------------------------------------
CARD_W, CARD_H = 958, 566
ART_X, ART_Y, ART_LH = 30, 42, 9.2       # portrait origin / line height
ART_FS, ART_CW = 9, 5.4                   # portrait font size / advance width
PANEL_X, PANEL_Y, PANEL_STEP = 515, 40, 21.5
PANEL_FS = 13
DOT_W = 54                                # dotted-leader width in characters
FONT = "font-family=\"'JetBrains Mono','SF Mono',Consolas,Menlo,monospace\""
CYCLE = 10.0                              # master animation loop, seconds
RAIN_GLYPHS = "01<>/{}[]=+*ilcXUZ0O4%#@$abcdef2379"

# The matrix face always lives on a dark "screen" panel — in both themes — so
# the green portrait looks identical in light and dark mode.
SCREEN_X, SCREEN_Y = 16, 16
SCREEN_W, SCREEN_H = 470, CARD_H - 32
SCREEN_BG, SCREEN_BORDER = "#0a0e14", "#1d2530"
FACE_RAIN, FACE_RAIN_HEAD = "#2ea043", "#c5f7cd"


# ---------------------------------------------------------------------------
# GitHub stats
# ---------------------------------------------------------------------------
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ACCESS_TOKEN") or ""
PRIV_TOKEN = os.environ.get("ACCESS_TOKEN") or TOKEN


def gh(url, payload=None, token=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER}
    auth = token or TOKEN
    if auth:                       # public REST works token-free; never send an empty Bearer
        headers["Authorization"] = f"Bearer {auth}"
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode() if payload else None, headers=headers)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read() or "{}")


def graphql(query, variables=None, token=None):
    resp = gh("https://api.github.com/graphql",
              {"query": query, "variables": variables or {}}, token)
    if resp.get("errors"):
        raise RuntimeError(resp["errors"])
    return resp["data"]


STAT_KEYS = ("followers", "following", "repos", "private", "stars", "commits",
             "prs", "issues", "reviews", "contribs", "member", "age",
             "loc", "loc_add", "loc_del")


def blank_stats():
    return {k: None for k in STAT_KEYS}


def public_stats():
    """Token-free seed: REST public data only (followers, repos, stars, age)."""
    s = blank_stats()
    try:
        u = gh(f"https://api.github.com/users/{USER}")
        stars = repos = 0
        page = 1
        while True:
            batch = gh(f"https://api.github.com/users/{USER}/repos"
                       f"?per_page=100&page={page}&type=owner")
            if not batch:
                break
            for r in batch:
                if not r["fork"]:
                    stars += r["stargazers_count"]
                    repos += 1
            page += 1
        created = u.get("created_at", "")
        s.update(followers=u.get("followers", 0), following=u.get("following", 0),
                 repos=repos, stars=stars)
        if created:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            s["member"] = dt.strftime("%b %Y")
            s["age"] = datetime.now(timezone.utc).year - dt.year
    except Exception as e:
        print("public_stats failed:", e)
    return s


LOC_QUERY = """
query($owner: String!, $name: String!, $id: ID!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef { target { ... on Commit {
      history(first: 100, author: {id: $id}, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes { additions deletions }
      } } } } } }"""


def year_contribs():
    """Per-year contribution queries (one request each) to dodge the GraphQL
    RESOURCE_LIMITS that a single 10+ year aliased query triggers."""
    commits = prs = issues = reviews = contribs = 0
    for y in range(JOINED_YEAR, datetime.now(timezone.utc).year + 1):
        c = graphql(f'''query {{ user(login: "{USER}") {{
          contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y + 1}-01-01T00:00:00Z") {{
            totalCommitContributions restrictedContributionsCount
            totalPullRequestContributions totalIssueContributions
            totalPullRequestReviewContributions
            contributionCalendar {{ totalContributions }} }} }} }}'''
                     )["user"]["contributionsCollection"]
        commits += c["totalCommitContributions"] + c["restrictedContributionsCount"]
        prs += c["totalPullRequestContributions"]
        issues += c["totalIssueContributions"]
        reviews += c["totalPullRequestReviewContributions"]
        contribs += c["contributionCalendar"]["totalContributions"]
    return {"commits": commits, "prs": prs, "issues": issues,
            "reviews": reviews, "contribs": contribs}


def owned_repos(uid):
    """All non-fork owned repos (public + private), paginated."""
    nodes, cursor = [], None
    while True:
        page = graphql(f'''query($c: String) {{ user(login: "{USER}") {{
          repositories(first: 100, after: $c, ownerAffiliations: OWNER, isFork: false) {{
            totalCount pageInfo {{ hasNextPage endCursor }}
            nodes {{ name stargazerCount isPrivate }} }} }} }}''',
                       {"c": cursor}, token=PRIV_TOKEN)["user"]["repositories"]
        nodes += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            return nodes
        cursor = page["pageInfo"]["endCursor"]


def token_stats():
    """Full stats via GraphQL (needs a token; used in GitHub Actions)."""
    s = blank_stats()
    u = graphql(f'''query {{ user(login: "{USER}") {{
      id createdAt
      followers {{ totalCount }} following {{ totalCount }}
      pullRequests {{ totalCount }} issues {{ totalCount }}
    }} }}''', token=PRIV_TOKEN)["user"]
    dt = datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))
    s["member"] = dt.strftime("%b %Y")
    s["age"] = datetime.now(timezone.utc).year - dt.year
    s["followers"] = u["followers"]["totalCount"]
    s["following"] = u["following"]["totalCount"]
    s.update(year_contribs())
    # lifetime PR/issue authored counts are richer than per-year contribution sums
    s["prs"] = u["pullRequests"]["totalCount"]
    s["issues"] = u["issues"]["totalCount"]

    repos = owned_repos(u["id"])
    s["repos"] = len(repos)
    s["private"] = sum(1 for r in repos if r["isPrivate"])
    s["stars"] = sum(r["stargazerCount"] for r in repos)

    add = rem = 0
    for name in [r["name"] for r in repos]:
        cursor = None
        try:
            while True:
                ref = graphql(LOC_QUERY,
                              {"owner": USER, "name": name, "id": u["id"], "cursor": cursor},
                              token=PRIV_TOKEN)["repository"]["defaultBranchRef"]
                if ref is None:
                    break
                h = ref["target"]["history"]
                add += sum(n["additions"] for n in h["nodes"])
                rem += sum(n["deletions"] for n in h["nodes"])
                if not h["pageInfo"]["hasNextPage"]:
                    break
                cursor = h["pageInfo"]["endCursor"]
        except Exception as e:
            print(f"loc {name}: {e}")
    s["loc"], s["loc_add"], s["loc_del"] = add - rem, add, rem
    return s


def fetch_stats():
    if TOKEN:
        try:
            return token_stats()
        except Exception as e:
            print("token_stats failed, falling back to public:", e)
    return public_stats()


# ---------------------------------------------------------------------------
# Info-panel line model: each line is a list of (text, colour-key) segments.
# ---------------------------------------------------------------------------
def kv(key, val, width=DOT_W):
    val = str(val)
    dots = "." * max(width - len(key) - len(val) - 3, 1)
    return [(f"{key}: ", "k"), (dots + " ", "d"), (val, "v")]


def kv2(k1, v1, k2, v2):
    return kv(k1, v1, 30) + [("  ", "d")] + kv(k2, v2, 22)


def rule(title=""):
    label = f"- {title} " if title else ""
    return [(label, "h"), ("-" * (DOT_W - len(label)), "d")]


def num(x):
    return "—" if x is None else f"{x:,}"


def member_str(s):
    if not s.get("member"):
        return "—"
    age = f"  ·  {s['age']} yrs" if s.get("age") else ""
    return f"{s['member']}{age}"


def repos_str(s):
    if s.get("repos") is None:
        return "—"
    priv = f" ({s['private']} priv)" if s.get("private") else ""
    return f"{s['repos']}{priv}"


def info_lines(s):
    handle = INFO["handle"]
    return [
        [(f"{handle} ", "h"), ("-" * (DOT_W - len(handle) - 1), "d")],
        [],
        kv("Role", INFO["role"]),
        kv("Company", INFO["company"]),
        kv("Location", INFO["location"]),
        kv("Focus", INFO["focus"]),
        kv("Languages", INFO["languages"]),
        kv("Infra", INFO["infra"]),
        kv("Editor", INFO["editor"]),
        kv("Hobbies", INFO["hobbies"]),
        kv("Archival", INFO["archival"]),
        [],
        rule("Connect"),
        kv("LinkedIn", INFO["linkedin"]),
        kv("YouTube", INFO["youtube"]),
        kv("GitHub", INFO["github"]),
        [],
        rule("GitHub Stats"),
        kv("Member Since", member_str(s)),
        kv2("Repos", repos_str(s), "Stars", num(s["stars"])),
        kv2("Commits", num(s["commits"]), "Followers", num(s["followers"])),
        kv2("Pull Reqs", num(s["prs"]), "Issues", num(s["issues"])),
        kv2("Contribs", num(s["contribs"]), "Reviews", num(s["reviews"])),
        ([("Lines of Code: ", "k"), (num(s["loc"]), "v"), ("  ( ", "d"),
          (num(s["loc_add"]) + "++", "g"), (", ", "d"),
          (num(s["loc_del"]) + "--", "r"), (" )", "d")]
         if s["loc"] is not None else kv("Lines of Code", "—")),
    ]


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------
def esc(t):
    return html.escape(t, quote=True)


def face_color(lvl):
    """Phosphor-green ramp on the dark face 'screen': bright photo -> bright
    green, dark -> near-black green. Identical in light and dark themes because
    the face always sits on the same dark panel."""
    t = lvl / 25.0
    g = int(round(30 + 225 * t ** 0.9))
    r, b = int(g * 0.26), int(g * 0.5)
    return f"#{r:02x}{g:02x}{b:02x}"


def face_columns():
    """{col: [(row, glyph, level), ...]} for every inked cell."""
    cols = {}
    for r, (glyphs, levels) in enumerate(FACE):
        for c, ch in enumerate(glyphs):
            if ch != " ":
                lvl = LVL.index(levels[c]) if c < len(levels) else 0
                cols.setdefault(c, []).append((r, ch, lvl))
    return cols


def render_portrait(mode):
    """Each column is clipped by a rectangle that grows downward (reveal) and
    later slides down to nothing (melt), so the face crystallises column-by-
    column behind the rain and dissolves back into it every cycle."""
    top = ART_Y - ART_LH
    height = len(FACE) * ART_LH + ART_LH
    bottom = top + height
    rng = random.Random(SEED)
    cols = face_columns()
    ncols = max(cols) + 1
    defs, groups = [], []
    for c in sorted(cols):
        cx = ART_X + c * ART_CW
        cid = f"c{mode[0]}{c}"
        jitter = (c / ncols) * 1.3 + rng.uniform(0.0, 0.55)     # organic per-column stagger
        begin = f"{-CYCLE + 0.5 + jitter:.3f}s"
        defs.append(
            f'<clipPath id="{cid}"><rect x="{cx - 0.6:.1f}" width="{ART_CW + 0.8:.1f}" '
            f'y="{top:.1f}" height="0">'
            f'<animate attributeName="height" begin="{begin}" dur="{CYCLE}s" '
            f'repeatCount="indefinite" values="0;0;{height:.0f};{height:.0f};0;0" '
            f'keyTimes="0;0.12;0.32;0.80;0.95;1"/>'
            f'<animate attributeName="y" begin="{begin}" dur="{CYCLE}s" '
            f'repeatCount="indefinite" '
            f'values="{top:.0f};{top:.0f};{top:.0f};{bottom:.0f};{bottom:.0f}" '
            f'keyTimes="0;0.32;0.80;0.95;1"/>'
            f'</rect></clipPath>')
        cells = "".join(
            f'<tspan x="{cx:.1f}" y="{ART_Y + r * ART_LH:.1f}" '
            f'fill="{face_color(lvl)}">{esc(ch)}</tspan>'
            for r, ch, lvl in cols[c])
        groups.append(f'<text clip-path="url(#{cid})" xml:space="preserve">{cells}</text>')
    return (f'<defs>{"".join(defs)}</defs>'
            f'<g font-size="{ART_FS}px">{"".join(groups)}</g>')


def render_rain():
    """Green glyph streams falling over the portrait columns. Strong while the
    face is forming, faint while it holds, strong again as it melts."""
    rng = random.Random(SEED + 99)
    top = ART_Y - ART_LH
    span = len(FACE) * ART_LH + 150
    cols = face_columns()
    out = [f'<g font-size="{ART_FS}px">'
           f'<animate attributeName="opacity" dur="{CYCLE}s" repeatCount="indefinite" '
           f'values="0.9;1;1;0.85;0.1;0.1;0.85;1;0.9" '
           f'keyTimes="0;0.08;0.22;0.32;0.5;0.74;0.86;0.96;1"/>']
    for c in sorted(cols):
        if rng.random() > 0.55:               # ~45% of columns carry a stream
            continue
        x = ART_X + c * ART_CW
        length = rng.randint(7, 14)
        dur = rng.uniform(1.7, 3.4)
        delay = rng.uniform(-3.4, 0.0)
        tspans = []
        for j in range(length):
            ch = rng.choice(RAIN_GLYPHS)
            frac = j / max(1, length - 1)
            if j == length - 1:
                fill, op = FACE_RAIN_HEAD, 1.0
            else:
                fill, op = FACE_RAIN, round(0.08 + 0.62 * frac, 2)
            dy = "0" if j == 0 else f"{ART_LH:.1f}"
            tspans.append(f'<tspan x="{x:.1f}" dy="{dy}" fill="{fill}" '
                          f'opacity="{op}">{esc(ch)}</tspan>')
        out.append(
            f'<text y="{top:.1f}" xml:space="preserve">{"".join(tspans)}'
            f'<animateTransform attributeName="transform" type="translate" '
            f'dur="{dur:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite" '
            f'values="0 -80; 0 {span:.0f}"/></text>')
    out.append('</g>')
    return "\n".join(out)


def render_panel(p, stats):
    """Neofetch panel that types itself out like a terminal: each line wipes in
    left-to-right, staggered top-to-bottom, then a green caret blinks."""
    lines = info_lines(stats)
    reveal_w = CARD_W - PANEL_X - 16
    defs, body = ['<defs>'], []
    rank, last_y = 0, PANEL_Y
    for i, segs in enumerate(lines):
        if not segs:
            continue
        y = PANEL_Y + i * PANEL_STEP
        last_y = y
        begin = 0.4 + rank * 0.10
        cid = f"pl{i}"
        defs.append(
            f'<clipPath id="{cid}"><rect x="{PANEL_X - 3:.0f}" y="{y - 12:.0f}" '
            f'width="0" height="18"><animate attributeName="width" begin="{begin:.2f}s" '
            f'dur="0.34s" values="0;{reveal_w:.0f}" calcMode="spline" '
            f'keySplines=".2 0 .1 1" fill="freeze"/></rect></clipPath>')
        spans = "".join(f'<tspan fill="{p[c]}">{esc(t)}</tspan>' for t, c in segs)
        body.append(f'<text x="{PANEL_X}" y="{y:.1f}" clip-path="url(#{cid})" '
                    f'xml:space="preserve">{spans}</text>')
        rank += 1
    defs.append('</defs>')
    caret_y = last_y + PANEL_STEP
    caret_begin = 0.4 + rank * 0.10
    caret = (f'<rect x="{PANEL_X}" y="{caret_y - 11:.0f}" width="8" height="14" '
             f'fill="{p["g"]}" opacity="0"><animate attributeName="opacity" '
             f'begin="{caret_begin:.2f}s" dur="1.05s" values="0;1;1;0;0" '
             f'keyTimes="0;0.03;0.5;0.53;1" repeatCount="indefinite"/></rect>')
    return (f'<g font-size="{PANEL_FS}px">' + "\n".join(defs) + "\n"
            + "\n".join(body) + "\n" + caret + '</g>')


def render(mode, stats):
    p = PALETTES[mode]
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{CARD_H}" '
        f'viewBox="0 0 {CARD_W} {CARD_H}" {FONT} font-size="{PANEL_FS}px">',
        f'<rect x="0.5" y="0.5" width="{CARD_W - 1}" height="{CARD_H - 1}" '
        f'rx="12" fill="{p["bg"]}" stroke="{p["border"]}"/>',
        # dark "screen" behind the face, clipped so rain never spills past it
        f'<clipPath id="scr"><rect x="{SCREEN_X}" y="{SCREEN_Y}" width="{SCREEN_W}" '
        f'height="{SCREEN_H}" rx="10"/></clipPath>',
        f'<rect x="{SCREEN_X}" y="{SCREEN_Y}" width="{SCREEN_W}" height="{SCREEN_H}" '
        f'rx="10" fill="{SCREEN_BG}" stroke="{SCREEN_BORDER}"/>',
        f'<g clip-path="url(#scr)">',
        render_rain(),
        render_portrait(mode),
        '</g>',
        render_panel(p, stats),
        '</svg>',
    ])


def selfcheck():
    assert len("".join(t for t, _ in kv("Role", INFO["role"]))) == DOT_W
    assert FACE and all(len(g) == len(l) for g, l in FACE), "grid glyph/level mismatch"


if __name__ == "__main__":
    selfcheck()
    stats = fetch_stats()
    print("stats:", stats)
    for mode in PALETTES:
        with open(f"{mode}_mode.svg", "w", encoding="utf-8") as f:
            f.write(render(mode, stats))
    print("wrote dark_mode.svg, light_mode.svg")
