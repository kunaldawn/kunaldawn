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
import time
import urllib.request
from datetime import datetime, timedelta, timezone

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
        # contribution-graph ramp, none -> most
        "heat": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
        "heat_edge": "#21262d",
    },
    "light": {
        "light": True,
        "bg": "#ffffff", "border": "#d0d7de",
        "h": "#0969da", "k": "#953800", "v": "#24292f", "d": "#afb8c1",
        "g": "#1a7f37", "r": "#cf222e",
        "rain": "#1a7f37", "rain_head": "#0a3d1a",
        "heat": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "heat_edge": "#d0d7de",
    },
}

# --- geometry ---------------------------------------------------------------
# CARD_H is derived from the panel content (see layout()); the portrait is then
# centred vertically in whatever screen height that leaves.
MIN_CARD_H = 566
ART_LH, ART_FS, ART_CW = 9.2, 9, 5.4      # portrait line height / font / advance
MAX_FACE_SCALE = 1.25                     # cap so glyphs stay crisp
GUTTER = 28                               # screen -> panel gap
PANEL_Y, PANEL_STEP = 40, 19.0
CARD_W = PANEL_X = 0                      # both derived in layout()
PANEL_FS = 13
CH_W = PANEL_FS * 0.6                     # mono advance width at PANEL_FS
DOT_W = 54                                # dotted-leader width in characters
PANEL_W = DOT_W * CH_W                    # panel width in px (graphics span this)
HEAT_KEY_W = 96                           # gutter for the heatmap less/more key
FONT = "font-family=\"'JetBrains Mono','SF Mono',Consolas,Menlo,monospace\""
CYCLE = 10.0                              # master animation loop, seconds
PULSE_DUR = 9.0                           # section-rule packet loop, seconds
RAIN_GLYPHS = "01<>/{}[]=+*ilcXUZ0O4%#@$abcdef2379"

# The matrix face always lives on a dark "screen" panel — in both themes — so
# the green portrait looks identical in light and dark mode.
SCREEN_X, SCREEN_Y = 16, 16
SCREEN_BG, SCREEN_BORDER = "#0a0e14", "#1d2530"
FACE_RAIN, FACE_RAIN_HEAD = "#2ea043", "#c5f7cd"


# ---------------------------------------------------------------------------
# GitHub stats
# ---------------------------------------------------------------------------
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ACCESS_TOKEN") or ""
PRIV_TOKEN = os.environ.get("ACCESS_TOKEN") or TOKEN


def gh(url, payload=None, token=None, tries=4):
    """One API call, retried with backoff. A long stats run makes thousands of
    requests; a single dropped connection used to abandon the whole token path
    and fall back to public-only numbers."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER}
    auth = token or TOKEN
    if auth:                       # public REST works token-free; never send an empty Bearer
        headers["Authorization"] = f"Bearer {auth}"
    body = json.dumps(payload).encode() if payload else None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, data=body, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read() or "{}")
        except Exception as e:
            if attempt == tries - 1:
                raise
            print(f"  retry {attempt + 1}/{tries - 1} after {e}")
            time.sleep(2 ** attempt)


def graphql(query, variables=None, token=None):
    resp = gh("https://api.github.com/graphql",
              {"query": query, "variables": variables or {}}, token)
    if resp.get("errors"):
        raise RuntimeError(resp["errors"])
    return resp["data"]


STAT_KEYS = ("followers", "following", "repos", "private", "stars", "commits",
             "prs", "issues", "reviews", "contribs", "member", "age",
             "loc", "loc_add", "loc_del",
             "langs", "cal", "cal_months", "streak", "longest", "best_day",
             "active_days", "cal_days")

# linguist colours for the token-free fallback, where the API gives no colour
LANG_COLOR = {
    "Go": "#00ADD8", "Python": "#3572A5", "C": "#555555", "C++": "#f34b7d",
    "Rust": "#dea584", "Java": "#b07219", "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a", "Shell": "#89e051", "HTML": "#e34c26",
    "CSS": "#563d7c", "Jupyter Notebook": "#DA5B0B", "Kotlin": "#A97BFF",
    "Swift": "#F05138", "Dart": "#00B4AB", "PHP": "#4F5D95", "Ruby": "#701516",
    "C#": "#178600", "Makefile": "#427819", "CMake": "#DA3434",
    "Vue": "#41b883", "Lua": "#000080", "Verilog": "#b2b7f8",
}
GREY = "#8b949e"


def blank_stats():
    return {k: None for k in STAT_KEYS}


def top_langs(sizes, colors, k=6):
    """[(name, fraction, colour)] for the k biggest languages, plus 'Other'."""
    total = sum(sizes.values())
    if not total:
        return None
    ranked = sorted(sizes.items(), key=lambda kv: -kv[1])
    out = [(n, v / total, colors.get(n) or LANG_COLOR.get(n, GREY))
           for n, v in ranked[:k]]
    rest = total - sum(v for _, v in ranked[:k])
    if rest > 0:
        out.append(("Other", rest / total, GREY))
    return out


def public_stats():
    """Token-free seed: REST public data only (followers, repos, stars, age)."""
    s = blank_stats()
    try:
        u = gh(f"https://api.github.com/users/{USER}")
        stars = repos = 0
        page = 1
        sizes = {}
        while True:
            batch = gh(f"https://api.github.com/users/{USER}/repos"
                       f"?per_page=100&page={page}&type=owner")
            if not batch:
                break
            for r in batch:
                if not r["fork"]:
                    stars += r["stargazers_count"]
                    repos += 1
                    if r.get("language"):     # no byte counts here; size-weighted
                        sizes[r["language"]] = sizes.get(r["language"], 0) + max(r.get("size", 1), 1)
            page += 1
        s["langs"] = top_langs(sizes, {})
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


TZ = timezone(timedelta(hours=5, minutes=30))   # bucket commits by local day

# History authored by the user on one branch, private repos included. Every
# branch is walked, not just the default one, so work that never landed on main
# still counts; commits are deduped by SHA, so a branch that was merged
# contributes its commits exactly once. This single walk feeds the commit count,
# the LOC totals and the activity grid, so the card reports what the repos
# actually contain rather than what GitHub's contribution rules credit.
# `additions`/`deletions` are occasionally SERVICE_UNAVAILABLE on GitHub's side
# and fail the whole query, so HIST_LITE is the retry that still gets the dates.
BRANCH_QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    refs(refPrefix: "refs/heads/", first: 100, after: $cursor) {
      pageInfo { hasNextPage endCursor } nodes { name } } } }"""

HIST_QUERY = """
query($owner: String!, $name: String!, $id: ID!, $ref: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    ref(qualifiedName: $ref) { target { ... on Commit {
      history(first: 100, author: {id: $id}, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes { oid committedDate additions deletions }
      } } } } } }"""

HIST_LITE = HIST_QUERY.replace(" additions deletions", "")


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
    """All non-fork owned repos (public + private), paginated, with per-repo
    language byte counts."""
    nodes, cursor = [], None
    while True:
        page = graphql(f'''query($c: String) {{ user(login: "{USER}") {{
          repositories(first: 100, after: $c, ownerAffiliations: OWNER, isFork: false) {{
            totalCount pageInfo {{ hasNextPage endCursor }}
            nodes {{ name stargazerCount isPrivate
              defaultBranchRef {{ name }}
              languages(first: 12, orderBy: {{field: SIZE, direction: DESC}}) {{
                edges {{ size node {{ name color }} }} }} }} }} }} }}''',
                       {"c": cursor}, token=PRIV_TOKEN)["user"]["repositories"]
        nodes += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            return nodes
        cursor = page["pageInfo"]["endCursor"]


def repo_langs(repos):
    """Aggregate language bytes across every owned repo."""
    sizes, colors = {}, {}
    for r in repos:
        for e in (r.get("languages") or {}).get("edges", []):
            name = e["node"]["name"]
            sizes[name] = sizes.get(name, 0) + e["size"]
            colors[name] = e["node"]["color"] or LANG_COLOR.get(name, GREY)
    return top_langs(sizes, colors)


def branch_names(name, default=None):
    """Every head ref of a repo, default branch first so that the branches which
    were merged into it hit the already-seen shortcut in walk_commits()."""
    out, cursor = [], None
    while True:
        page = graphql(BRANCH_QUERY, {"owner": USER, "name": name, "cursor": cursor},
                       token=PRIV_TOKEN)["repository"]["refs"]
        out += [n["name"] for n in page["nodes"]]
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    if default in out:
        out.remove(default)
        out.insert(0, default)
    return out


def walk_commits(name, uid, default, seen, daily):
    """Every commit the user authored in one repo, on ANY branch, deduped by SHA
    and bucketed into `daily` by local calendar day. Private repos are included
    as long as the token can see them. Returns (commits, +lines, -lines)."""
    n = add = rem = 0
    for br in branch_names(name, default):
        cursor, lite = None, False
        while True:
            v = {"owner": USER, "name": name, "id": uid, "ref": br, "cursor": cursor}
            try:
                ref = graphql(HIST_LITE if lite else HIST_QUERY, v,
                              token=PRIV_TOKEN)["repository"]["ref"]
            except Exception as e:
                if lite:                       # already the reduced query — give up
                    print(f"  {name}@{br}: {e}")
                    break
                lite = True                    # additions/deletions unavailable
                continue
            if ref is None:
                break
            h = ref["target"]["history"]
            fresh = 0
            for c in h["nodes"]:
                if c["oid"] in seen:
                    continue
                seen.add(c["oid"])
                fresh += 1
                n += 1
                add += c.get("additions", 0)
                rem += c.get("deletions", 0)
                day = datetime.fromisoformat(c["committedDate"]).astimezone(TZ).date()
                daily[day] = daily.get(day, 0) + 1
            # a whole page already seen means this branch has rejoined history
            # walked earlier; its ancestors are all counted, so stop paging
            if fresh == 0 or not h["pageInfo"]["hasNextPage"]:
                break
            cursor = h["pageInfo"]["endCursor"]
    return n, add, rem


def commit_calendar(daily):
    """A 53-column Sunday-first grid of the last year of real commits, plus the
    streak figures derived from it."""
    today = datetime.now(TZ).date()
    start = today - timedelta(days=364)
    start -= timedelta(days=(start.weekday() + 1) % 7)      # back up to Sunday

    grid, months, seen_month = [], [], None
    day = start
    while day <= today:
        cells = [None] * 7
        for i in range(7):
            d = day + timedelta(days=i)
            if start <= d <= today:
                cells[i] = daily.get(d, 0)
        grid.append(cells)
        if day.month != seen_month and (not months or len(grid) - months[-1][0] >= 3):
            months.append((len(grid) - 1, day.strftime("%b")))
            seen_month = day.month
        day += timedelta(days=7)

    days = [daily.get(start + timedelta(days=i), 0)
            for i in range((today - start).days + 1)]
    longest = run = 0
    for c in days:
        run = run + 1 if c else 0
        longest = max(longest, run)
    tail = days[:-1] if days and days[-1] == 0 else days   # today may not be done yet
    streak = 0
    for c in reversed(tail):
        if not c:
            break
        streak += 1
    return {"cal": grid, "cal_months": months, "streak": streak,
            "longest": longest, "best_day": max(days) if days else 0,
            "active_days": sum(1 for c in days if c), "cal_days": len(days)}


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
    s["langs"] = repo_langs(repos)

    # one history walk per repo feeds commits, LOC and the activity grid
    seen, daily = set(), {}
    commits = add = rem = 0
    for r in repos:
        name = r["name"]
        n, a, d = walk_commits(name, u["id"],
                               (r.get("defaultBranchRef") or {}).get("name"),
                               seen, daily)
        commits += n
        add += a
        rem += d
    s["commits"] = commits
    s["loc"], s["loc_add"], s["loc_del"] = add - rem, add, rem
    s.update(commit_calendar(daily))
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
    """A section rule. Rendered as text plus a packet that rides the dashes."""
    label = f"- {title} " if title else ""
    return {"kind": "rule", "label": len(label),
            "segs": [(label, "h"), ("-" * (DOT_W - len(label)), "d")]}


def num(x):
    """Human-readable short form: 942, 4.8K, 12K, 340K, 1.4M."""
    if x is None:
        return "—"
    sign, n = ("-" if x < 0 else ""), abs(float(x))
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= div:
            v = n / div
            return f"{sign}{v:.1f}{suf}" if v < 10 else f"{sign}{v:.0f}{suf}"
    return f"{sign}{n:.0f}"


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


def lang_legend(langs):
    """Pack '● Name 41.2%' chips into at most two DOT_W-wide lines."""
    lines, cur, used = [], [], 0
    for name, frac, color in langs:
        chip = f"{name} {frac * 100:.1f}%"
        cost = len(chip) + 4                     # bullet + space + two-space gap
        if used + cost > DOT_W and cur:
            lines.append(cur)
            cur, used = [], 0
            if len(lines) == 2:
                break
        cur += [("● ", color), (chip + "  ", "v")]
        used += cost
    if cur and len(lines) < 2:
        lines.append(cur)
    return lines


def info_lines(s):
    handle = INFO["handle"]
    lines = [
        [(f"{handle} ", "h"), ("-" * (DOT_W - len(handle) - 1), "d")],
        [],
        kv("Role", INFO["role"]),
        kv("Organization", INFO["company"]),
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

    if s.get("langs"):
        lines += [[], rule("Code Composition"),
                  {"kind": "bar", "segs": s["langs"], "slots": 1}]
        lines += lang_legend(s["langs"])

    if s.get("cal"):
        span = f"last {len(s['cal'])} weeks"
        active = f"{s['active_days']} / {s['cal_days']} d"
        lines += [
            [], rule(f"Commit Activity · {span}"),
            {"kind": "heat", "weeks": s["cal"],
             "months": s.get("cal_months") or [], "slots": 3},
            kv2("Streak", f"{s['streak']} d", "Longest", f"{s['longest']} d"),
            kv2("Best Day", num(s["best_day"]), "Active", active),
        ]
    return lines


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


def layout(lines):
    """Derive the whole card from the panel content: the panel sets the height,
    the portrait scales up to fill that height (capped), and the card width
    follows the portrait. Sets CARD_W / PANEL_X, which the renderers read."""
    global CARD_W, PANEL_X
    slots = sum(line.get("slots", 1) if isinstance(line, dict) else 1
                for line in lines)
    card_h = max(int(PANEL_Y + slots * PANEL_STEP + 28), MIN_CARD_H)
    screen_h = card_h - 2 * SCREEN_Y

    ncols = max(face_columns()) + 1
    face_w, face_h = ncols * ART_CW, len(FACE) * ART_LH
    scale = min((screen_h - 44) / face_h, MAX_FACE_SCALE)
    lh, cw, fs = ART_LH * scale, ART_CW * scale, ART_FS * scale
    screen_w = face_w * scale + 34

    PANEL_X = SCREEN_X + screen_w + GUTTER
    CARD_W = int(PANEL_X + PANEL_W + 26)
    return {"card_h": card_h, "screen_w": screen_w, "screen_h": screen_h,
            "art_x": SCREEN_X + (screen_w - face_w * scale) / 2,
            "art_y": SCREEN_Y + (screen_h - face_h * scale) / 2 + lh,
            "lh": lh, "cw": cw, "fs": fs}


def render_portrait(L):
    """Face crystallises column-by-column behind the rain: each column wipes in
    top-to-bottom, holds, then melts away top-to-bottom.

    This reproduces the ORIGINAL clip-path crystallise EXACTLY — same per-column
    stagger, same reveal/hold/melt timing (0.12/0.32/0.80/0.95 of the cycle), same
    top-to-bottom wipe — but drives it with per-cell opacity instead of an animated
    <clipPath>. WebKit/Safari silently drops animated clipPath geometry in an SVG
    loaded as an <img>, which rendered the whole face blank on Apple devices; opacity
    animates identically everywhere. Each cell reveals/melts as the (former clip)
    frontier would have passed its row, so the visible result is unchanged."""
    art_x, art_y, lh, cw = L["art_x"], L["art_y"], L["lh"], L["cw"]
    top = art_y - lh
    height = len(FACE) * lh + lh
    rng = random.Random(SEED)
    cols = face_columns()
    ncols = max(cols) + 1
    out = [f'<g font-size="{L["fs"]:.2f}px">']
    for c in sorted(cols):
        cx = art_x + c * cw
        jitter = (c / ncols) * 1.3 + rng.uniform(0.0, 0.55)     # identical per-column stagger
        begin = f"{-CYCLE + 0.5 + jitter:.3f}s"
        cells = []
        for r, ch, lvl in cols[c]:
            y = art_y + r * lh
            frac = (y - top) / height                            # row position along the wipe
            rs = 0.12 + frac * 0.20                               # reveal frontier reaches this row
            ms = 0.80 + frac * 0.15                               # melt frontier reaches this row
            kt = f"0;{rs - 0.006:.4f};{rs:.4f};{ms:.4f};{ms + 0.006:.4f};1"
            cells.append(
                f'<text x="{cx:.1f}" y="{y:.1f}" fill="{face_color(lvl)}" opacity="0" '
                f'xml:space="preserve">{esc(ch)}'
                f'<animate attributeName="opacity" begin="{begin}" dur="{CYCLE}s" '
                f'repeatCount="indefinite" values="0;0;1;1;0;0" keyTimes="{kt}"/></text>')
        out.append("".join(cells))
    out.append('</g>')
    return "\n".join(out)


def render_rain(L):
    """Green glyph streams falling over the portrait columns. Strong while the
    face is forming, faint while it holds, strong again as it melts. The streams
    span the whole screen, not just the face, so the padding around a centred
    portrait still rains."""
    rng = random.Random(SEED + 99)
    lh, cw = L["lh"], L["cw"]
    top = SCREEN_Y - lh
    span = L["screen_h"] + 120
    cols = face_columns()
    out = [f'<g font-size="{L["fs"]:.2f}px">'
           f'<animate attributeName="opacity" dur="{CYCLE}s" repeatCount="indefinite" '
           f'values="0.9;1;1;0.85;0.1;0.1;0.85;1;0.9" '
           f'keyTimes="0;0.08;0.22;0.32;0.5;0.74;0.86;0.96;1"/>']
    for c in sorted(cols):
        if rng.random() > 0.55:               # ~45% of columns carry a stream
            continue
        x = L["art_x"] + c * cw
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
            dy = "0" if j == 0 else f"{lh:.1f}"
            tspans.append(f'<tspan x="{x:.1f}" dy="{dy}" fill="{fill}" '
                          f'opacity="{op}">{esc(ch)}</tspan>')
        out.append(
            f'<text y="{top:.1f}" xml:space="preserve">{"".join(tspans)}'
            f'<animateTransform attributeName="transform" type="translate" '
            f'dur="{dur:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite" '
            f'values="0 -80;0 {span:.0f}"/></text>')
    out.append('</g>')
    return "\n".join(out)


def col(p, c):
    """Segment colour: a palette key, or a literal '#rrggbb' (language chips)."""
    return c if c.startswith("#") else p[c]


def fade(begin, dur=0.5):
    return (f'<animate attributeName="opacity" begin="{begin:.2f}s" dur="{dur}s" '
            f'values="0;1" calcMode="spline" keySplines=".3 0 .3 1" fill="freeze"/>')


def rule_line(p, line, y, begin, idx):
    """Section rule, with a short bright packet riding the dashes left to right
    on a slow loop — the dotted rule read as a bus, one packet on it."""
    spans = "".join(f'<tspan fill="{col(p, c)}">{esc(t)}</tspan>'
                    for t, c in line["segs"])
    x0 = PANEL_X + line["label"] * CH_W
    travel = (DOT_W - line["label"]) * CH_W - 16
    return (f'<text x="{PANEL_X}" y="{y:.1f}" opacity="0" xml:space="preserve">'
            f'{spans}{fade(begin)}</text>'
            f'<rect x="{x0:.1f}" y="{y - 4:.1f}" width="14" height="1.6" rx="0.8" '
            f'fill="{p["g"]}" opacity="0">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'dur="{PULSE_DUR}s" begin="{2.0 + idx * 1.7:.2f}s" '
            f'repeatCount="indefinite" values="0 0;{travel:.0f} 0" '
            f'calcMode="spline" keySplines=".45 0 .55 1"/>'
            f'<animate attributeName="opacity" dur="{PULSE_DUR}s" '
            f'begin="{2.0 + idx * 1.7:.2f}s" repeatCount="indefinite" '
            f'values="0;0.85;0.85;0;0" keyTimes="0;0.08;0.72;0.85;1"/></rect>')


def lang_bar(p, langs, y, begin):
    """Full-width stacked bar of language shares, rounded via a clip rect."""
    h, top = 11, y - 11
    out = [f'<g opacity="0">{fade(begin)}',
           f'<clipPath id="langclip"><rect x="{PANEL_X}" y="{top}" '
           f'width="{PANEL_W:.1f}" height="{h}" rx="{h / 2}"/></clipPath>',
           f'<g clip-path="url(#langclip)">']
    x = float(PANEL_X)
    for i, (_, frac, color) in enumerate(langs):
        w = PANEL_W * frac
        if i == len(langs) - 1:                 # absorb rounding into the last one
            w = PANEL_X + PANEL_W - x
        out.append(f'<rect x="{x:.2f}" y="{top}" width="{max(w, 0.6):.2f}" '
                   f'height="{h}" fill="{color}"/>')
        x += w
    out.append('</g></g>')
    return "".join(out)


def heat_levels(weeks):
    """Bucket day counts the way GitHub does: quartiles of the days that HAVE
    contributions, not fractions of the peak day. Scaling against the peak makes
    one outlier day (111 commits) push every ordinary day into the palest green;
    quartiles keep the grid's contrast where the actual distribution is."""
    vals = sorted(c for w in weeks for c in w if c)
    if not vals:
        return []
    return [vals[min(int(len(vals) * f), len(vals) - 1)] for f in (0.25, 0.5, 0.75)]


def heat_map(p, weeks, months, y, begin):
    """GitHub-style 7-row contribution grid, one column per week. The grid fills
    the panel width minus a right-hand gutter for the less/more key."""
    step = (PANEL_W - HEAT_KEY_W) / max(len(weeks), 1)
    cell = step - 1.5                        # ~25% gap, as on github.com
    top = y - 6
    cuts = heat_levels(weeks)
    ramp = p["heat"]
    out = [f'<g opacity="0">{fade(begin, 0.6)}']
    for wi, name in months:                  # month ticks above the grid
        out.append(f'<text x="{PANEL_X + wi * step:.1f}" y="{top - 4:.1f}" '
                   f'font-size="8.5px" fill="{p["d"]}">{name}</text>')
    for wi, week in enumerate(weeks):
        for di, count in enumerate(week):
            if count is None:                # day outside the queried range
                continue
            lvl = 0 if not count else 1 + sum(1 for c in cuts if count > c)
            out.append(
                f'<rect x="{PANEL_X + wi * step:.2f}" y="{top + di * step:.2f}" '
                f'width="{cell:.2f}" height="{cell:.2f}" rx="1.1" fill="{ramp[lvl]}"/>')
    # key: less [][][][][] more, in the gutter, centred on the grid
    kc, kstep = 5.5, 7.0
    lx = PANEL_X + len(weeks) * step + 10
    ly = top + (7 * step - kc) / 2
    out.append(f'<text x="{lx:.1f}" y="{ly + 5:.1f}" font-size="9px" '
               f'fill="{p["d"]}">less</text>')
    for i, c in enumerate(ramp):
        out.append(f'<rect x="{lx + 25 + i * kstep:.1f}" y="{ly:.1f}" width="{kc}" '
                   f'height="{kc}" rx="1.2" fill="{c}"/>')
    out.append(f'<text x="{lx + 25 + 5 * kstep + 3:.1f}" y="{ly + 5:.1f}" '
               f'font-size="9px" fill="{p["d"]}">more</text>')
    out.append('</g>')
    return "".join(out)


def render_panel(p, lines):
    """Neofetch panel that prints itself line-by-line (each line fades in,
    staggered top-to-bottom), then a green caret blinks. Opacity-only: the
    original left-to-right clip-path 'typing' wipe also blanked on Safari/WebKit
    (animated clipPath), so the reveal is done with opacity, which animates
    everywhere. Graphic rows (language bar, contribution grid) join the same
    stagger and consume `slots` line heights."""
    body = []
    rank, slot, rules = 0, 0, 0
    for line in lines:
        y = PANEL_Y + slot * PANEL_STEP
        if isinstance(line, dict):
            begin = 0.4 + rank * 0.09
            if line["kind"] == "bar":
                body.append(lang_bar(p, line["segs"], y, begin))
            elif line["kind"] == "heat":
                body.append(heat_map(p, line["weeks"], line["months"], y, begin))
            elif line["kind"] == "rule":
                body.append(rule_line(p, line, y, begin, rules))
                rules += 1
            slot += line.get("slots", 1)
            rank += 1
            continue
        if line:
            spans = "".join(f'<tspan fill="{col(p, c)}">{esc(t)}</tspan>'
                            for t, c in line)
            body.append(
                f'<text x="{PANEL_X}" y="{y:.1f}" opacity="0" xml:space="preserve">'
                f'{spans}{fade(0.4 + rank * 0.09)}</text>')
            rank += 1
        slot += 1
    caret_y = PANEL_Y + slot * PANEL_STEP
    caret_begin = 0.4 + rank * 0.09
    caret = (f'<rect x="{PANEL_X}" y="{caret_y - 11:.0f}" width="8" height="14" '
             f'fill="{p["g"]}" opacity="0"><animate attributeName="opacity" '
             f'begin="{caret_begin:.2f}s" dur="1.05s" values="0;1;1;0;0" '
             f'keyTimes="0;0.03;0.5;0.53;1" repeatCount="indefinite"/></rect>')
    return (f'<g font-size="{PANEL_FS}px">' + "\n".join(body) + "\n" + caret + '</g>')


def render(mode, stats):
    p = PALETTES[mode]
    lines = info_lines(stats)
    L = layout(lines)
    card_h, screen_w, screen_h = L["card_h"], L["screen_w"], L["screen_h"]
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{card_h}" '
        f'viewBox="0 0 {CARD_W} {card_h}" {FONT} font-size="{PANEL_FS}px">',
        f'<rect x="0.5" y="0.5" width="{CARD_W - 1}" height="{card_h - 1}" '
        f'rx="12" fill="{p["bg"]}" stroke="{p["border"]}"/>',
        # dark "screen" behind the face, clipped so rain never spills past it
        f'<clipPath id="scr"><rect x="{SCREEN_X}" y="{SCREEN_Y}" width="{screen_w:.1f}" '
        f'height="{screen_h}" rx="10"/></clipPath>',
        f'<rect x="{SCREEN_X}" y="{SCREEN_Y}" width="{screen_w:.1f}" height="{screen_h}" '
        f'rx="10" fill="{SCREEN_BG}" stroke="{SCREEN_BORDER}"/>',
        f'<g clip-path="url(#scr)">',
        render_rain(L),
        render_portrait(L),
        '</g>',
        render_panel(p, lines),
        '</svg>',
    ])


def selfcheck():
    assert len("".join(t for t, _ in kv("Role", INFO["role"]))) == DOT_W
    assert FACE and all(len(g) == len(l) for g, l in FACE), "grid glyph/level mismatch"
    assert num(0) == "0" and num(942) == "942" and num(4832) == "4.8K"
    assert num(12400) == "12K" and num(1_420_000) == "1.4M" and num(None) == "—"
    # a full-fat panel must still fit inside the card it sizes
    demo = blank_stats()
    demo.update(langs=[("Go", 0.6, "#00ADD8"), ("Python", 0.4, "#3572A5")],
                cal=[[0] * 7] * 53, streak=1, longest=1, best_day=1,
                active_days=1, cal_days=365)
    L = layout(info_lines(demo))
    assert PANEL_X + PANEL_W < CARD_W - 8, "panel overflows the card width"
    assert L["art_y"] > SCREEN_Y, "portrait pushed off the screen panel"


if __name__ == "__main__":
    selfcheck()
    stats = fetch_stats()
    print("stats:", {k: v for k, v in stats.items() if k != "cal"})
    for mode in PALETTES:
        with open(f"{mode}_mode.svg", "w", encoding="utf-8") as f:
            f.write(render(mode, stats))
    print("wrote dark_mode.svg, light_mode.svg")
