"""Step 7: page geometry (data/site_geo.json: hexagons placed over Great Britain in Web Mercator so they look regular, real
simplified boundaries, label points, nation labels) and index.html from code/page_template.html + code/page.css, filled from
data/results.json. 10.5281/zenodo.24104518, https://doi.org/10.5281/zenodo.24104518 and https://blog.tristanhotham.com/2026/10/31/petition-places/ are left for the publisher to fill."""
import math
import numpy as np, pandas as pd
from shapely.geometry import shape
from common import *

R = jload(f"{DATA}/results.json")
S = jload(f"{DATA}/site.json")
codes = [s["c"] for s in S["seats"]]
SE = pd.read_csv(f"{DATA}/seats.csv").set_index("code").loc[codes]
q, r = SE.q.values, SE.r.values
HX = np.sqrt(3) * (q + 0.5 * (r % 2)); HY = 1.5 * r
RE = 6378137.0
def merc_y(lat): return RE * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
def inv(x, y): return [round(math.degrees(x / RE), 5), round(math.degrees(2 * math.atan(math.exp(y / RE)) - math.pi / 2), 5)]
s = (merc_y(58.7) - merc_y(49.9)) / (HY.max() - HY.min() + 2)
cx, cy = RE * math.radians(-2.4), merc_y(54.35)
mx, my = (HX.max() + HX.min()) / 2, (HY.max() + HY.min()) / 2
ang = np.radians(np.arange(7) * 60 + 30)
hexf, ph = [], []
for i, (x, y) in enumerate(zip(HX, HY)):
    X, Y = cx + (x - mx) * s, cy + (y - my) * s
    ring = [inv(X + math.cos(a) * 0.985 * s, Y + math.sin(a) * 0.985 * s) for a in ang]
    c = inv(X, Y)
    hexf.append({"type": "Feature", "properties": {"i": i, "c": c}, "geometry": {"type": "Polygon", "coordinates": [ring]}})
    ph.append({"type": "Feature", "properties": {"n": SE.name.iloc[i]}, "geometry": {"type": "Point", "coordinates": c}})
allx = [p[0] for f in hexf for p in f["geometry"]["coordinates"][0]]; ally = [p[1] for f in hexf for p in f["geometry"]["coordinates"][0]]
bounds = [[min(allx), min(ally)], [max(allx), max(ally)]]
G = jload(f"{DATA}/seats.geojson")
gi = {c: k for k, c in enumerate(codes)}
geo, pg = [], []
def rnd(x): return [rnd(y) for y in x] if isinstance(x[0], (list, tuple)) else [round(x[0], 3), round(x[1], 3)]
for f in G["features"]:
    i = gi[f["properties"]["code"]]
    g = f["geometry"]
    rp = shape(g).representative_point()
    c = [round(rp.x, 4), round(rp.y, 4)]
    geo.append({"type": "Feature", "properties": {"i": i, "c": c}, "geometry": {"type": g["type"], "coordinates": rnd(g["coordinates"])}})
    pg.append({"type": "Feature", "properties": {"n": SE.name.iloc[i]}, "geometry": {"type": "Point", "coordinates": c}})
nat = []
for nm, pre, dx, dy in (("Scotland", "S", -4.5, 0), ("Wales", "W", -4.5, 0), ("Northern Ireland", "N", 0, -4.5), ("England", "E", 6, 4)):
    m = np.array([c.startswith(pre) for c in codes])
    if nm == "Scotland":
        x, y = HX[m].min() + dx, HY[m].max() - 10
    elif nm == "Northern Ireland":
        x, y = HX[m].mean(), HY[m].min() + dy
    elif nm == "England":
        x, y = HX[m].max() + 1, HY[m].max() - 14
    else:
        x, y = HX[m].min() + dx, HY[m].mean()
    nat.append({"type": "Feature", "properties": {"n": nm}, "geometry": {"type": "Point", "coordinates": inv(cx + (x - mx) * s, cy + (y - my) * s)}})
    # keep every nation label inside the fitted view (about 2.5 hex units either side of its centre for the text)
    lo, hi = inv(cx + (x - 2.5 - mx) * s, cy + (y - my) * s), inv(cx + (x + 2.5 - mx) * s, cy + (y - my) * s)
    bounds = [[min(bounds[0][0], lo[0]), bounds[0][1]], [max(bounds[1][0], hi[0]), bounds[1][1]]]
jsave({"hex": {"type": "FeatureCollection", "features": hexf}, "geo": {"type": "FeatureCollection", "features": geo},
       "ph": {"type": "FeatureCollection", "features": ph}, "pg": {"type": "FeatureCollection", "features": pg},
       "nat": {"type": "FeatureCollection", "features": nat}, "bounds": bounds}, f"{DATA}/site_geo.json")

KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{CSS}}", open(os.path.join(ROOT, "code", "page.css"), encoding="utf-8").read())
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{BYLINE}}", BYLINE).replace("{{VERSION}}", "2026a")
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--") + BANNED:
    assert bad not in vis, bad
for fn in re.findall(r'src="(img/[^"]+)"', t):
    assert os.path.exists(os.path.join(ROOT, fn)), fn
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB; site_geo", os.path.getsize(f"{DATA}/site_geo.json") // 1024, "KB")
