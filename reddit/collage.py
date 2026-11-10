"""Reddit collage (r/dataisbeautiful style, light background): the topic each constituency over-signs most, and four
single-petition maps. Reads data/ and results.json; writes reddit/petition_places_collage.png (2400 px wide)."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize
import numpy as np, pandas as pd
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name()
PAPER, INK, MUT = "#F6EED8", "#2B2119", "#6E604E"
CMAP = LinearSegmentedColormap.from_list("d", ["#1F4E7A", "#2F6A9E", "#9DB9D3", "#EDE6D6", "#E8A890", "#B4442E", "#7A2414"])
plt.rcParams.update({"font.family": "Source Serif 4", "figure.facecolor": PAPER})
R = jload(f"{DATA}/results.json"); S = jload(f"{DATA}/site.json"); SG = jload(f"{DATA}/site_sig.json")
seats = S["seats"]; pets = {p["id"]: p for p in S["pets"]}; order = [p["id"] for p in S["pets"]]
q = np.array([s["q"] for s in seats]); r = np.array([s["r"] for s in seats])
HX = np.sqrt(3) * (q + 0.5 * (r % 2)); HY = 1.5 * r
ang = np.radians(np.arange(6) * 60 + 30)
POLYS = [np.c_[x + np.cos(ang) * 0.97, y + np.sin(ang) * 0.97] for x, y in zip(HX, HY)]
Tc = np.array(S["Tc"], float); T = S["T"]


def hexmap(ax, cols):
    ax.add_collection(PolyCollection(POLYS, facecolors=cols, edgecolors=PAPER, linewidths=0.4))
    ax.set_xlim(HX.min() - 2, HX.max() + 2); ax.set_ylim(HY.min() - 2, HY.max() + 2); ax.set_aspect("equal"); ax.axis("off")


def lq(pid):
    p = pets[pid]; s = np.array(SG["s"][order.index(pid)], float)
    e = Tc * p["ts"] / T
    return (s + p["al"]) / (e + p["al"])


fig = plt.figure(figsize=(16, 12), dpi=150)
fig.text(0.03, 0.965, "What each UK constituency signs", fontsize=40, fontweight="bold", family=DISP, color=INK, va="top")
fig.text(0.03, 0.905, f"{R['sample']['petitions']} Parliament petitions with about 3,000+ signatures ({R['inputs']['first_year']} to {R['inputs']['last_year']}), "
         f"{R['sample']['seat_signatures'] / 1e6:.1f} million signatures counted in all 650 seats. Each hexagon is one constituency.", fontsize=15, color=MUT, va="top")
ax = fig.add_axes([0.0, 0.07, 0.46, 0.78])
fams = [pets[s["t"][0][0]]["f"] for s in seats]
hexmap(ax, [FAMILY_COL[f] for f in fams])
ax.set_title("The topic of the petition each seat over-signed most", fontsize=16, color=INK, loc="left", x=0.08)
cnt = pd.Series(fams).value_counts()
lax = fig.add_axes([0.29, 0.585, 0.17, 0.245]); lax.axis("off")
for i, f in enumerate([f for f in FAMILIES if f in cnt.index]):
    y = 1 - i * 0.071
    lax.add_patch(plt.Rectangle((0, y - 0.03), 0.09, 0.04, color=FAMILY_COL[f], transform=lax.transAxes))
    lax.text(0.13, y - 0.01, f"{FAMILY_NAME[f]} ({cnt[f]})", fontsize=10, va="center", transform=lax.transAxes, color=INK)
lax.text(0, 1.05, "Topic (number of seats)", fontsize=11.5, color=MUT, transform=lax.transAxes)
CASES = [711355, 700138, 700005, 700036]
for k, pid in enumerate(CASES):
    a2 = fig.add_axes([0.58 + (k % 2) * 0.21, 0.49 - (k // 2) * 0.37, 0.19, 0.31])
    v = np.clip(np.log2(lq(pid)), -2, 2)
    hexmap(a2, CMAP(Normalize(-2, 2)(v)))
    c = R["cases"][str(pid)]; t = pets[pid]["a"]
    t = t if len(t) < 40 else t[:38].rsplit(" ", 1)[0] + "..."
    a2.set_title(f"{t}\n{c['n']:,} signatures", fontsize=11.5, color=INK, loc="left")
cax = fig.add_axes([0.62, 0.068, 0.30, 0.013])
g = np.linspace(-2, 2, 256); cax.imshow(g[None, :], cmap=CMAP, aspect="auto", extent=(-2, 2, 0, 1))
cax.set_xticks([-2, -1, 0, 1, 2]); cax.set_xticklabels(["1/4", "half", "usual", "2x", "4x+"], fontsize=10); cax.set_yticks([])
for s_ in cax.spines.values(): s_.set_visible(False)
cax.set_title("Right: signatures against the seat's usual share of all petition signing", fontsize=11, color=MUT, loc="left")
fig.text(0.03, 0.018, "Data: UK Parliament petitions site (Open Government Licence v3.0); hexagons: Open Innovations (MIT). "
         "Dr Tristan Hotham · maps.tristanhotham.com/petition-places", fontsize=11, family="IBM Plex Mono", color=MUT)
out = os.path.join(ROOT, "reddit", "petition_places_collage.png")
fig.savefig(out, dpi=150, facecolor=PAPER)
from PIL import Image
print(out, Image.open(out).size)
