"""Step 6: figures for the page (img/*.jpg), the blog (release/blog/b_*.png, 1800 px), the paper (release/paper/f_*.pdf,
vector) and header.png (1200 x 630). Light paper background. Hexmap: one hex per 2024 constituency (Open Innovations)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm, Normalize
import numpy as np, pandas as pd
from PIL import Image
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF = "Source Serif 4"; DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name(); MONO = "IBM Plex Mono"
PAPER, INK, MUT, RULE = "#F6EED8", "#2B2119", "#6E604E", "#D9C9A3"
RED, BLUE, GREY, GOLD = "#B4442E", "#2F6A9E", "#9C9384", "#C98A2B"
CMAP = LinearSegmentedColormap.from_list("d", ["#1F4E7A", BLUE, "#9DB9D3", "#EDE6D6", "#E8A890", RED, "#7A2414"])
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.unicode_minus": False,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
R = jload(f"{DATA}/results.json")
Z = np.load(f"{SCR}/mat.npz", allow_pickle=True)
M, EB = Z["M"], Z["EB"]; codes = list(Z["codes"]); pids = [int(x) for x in Z["pids"]]
SE = pd.read_csv(f"{DATA}/seats.csv").set_index("code").loc[codes]
PR = pd.read_csv(f"{DATA}/seat_profiles.csv").set_index("code").loc[codes]
PM = pd.read_csv(f"{DATA}/petition_measures.csv").set_index("id")
P = pd.read_csv(f"{DATA}/petitions.csv").set_index("id")
BLOG, PAPD = f"{REL}/blog", f"{REL}/paper"
SRC = "Data: UK Parliament petitions (Open Government Licence v3.0), 734 petitions with about 3,000+ signatures, 2024 to 2026; hexes: Open Innovations\nmaps.tristanhotham.com/petition-places"

# hex geometry (odd-r offset rows, pointy top)
q, r = SE.q.values, SE.r.values
HX = np.sqrt(3) * (q + 0.5 * (r % 2)); HY = 1.5 * r
ang = np.radians(np.arange(6) * 60 + 30)
VX, VY = np.cos(ang), np.sin(ang)
POLYS = [np.c_[x + VX * 0.98, y + VY * 0.98] for x, y in zip(HX, HY)]


def hexmap(ax, colors, edge=PAPER, lw=0.25, labels=True):
    pc = PolyCollection(POLYS, facecolors=colors, edgecolors=edge, linewidths=lw)
    ax.add_collection(pc)
    ax.set_xlim(HX.min() - 2, HX.max() + 2); ax.set_ylim(HY.min() - 2, HY.max() + 2); ax.set_aspect("equal"); ax.axis("off")
    if labels:
        ni = np.array([c.startswith("N") for c in codes]); wa = np.array([c.startswith("W") for c in codes]); sc_ = np.array([c.startswith("S") for c in codes])
        for txt, (x, y), ha in (("Scotland", (HX[sc_].min() - 1.5, HY[sc_].max() - 4), "right"), ("Northern\nIreland", (HX[ni].min(), HY[ni].min() - 3.2), "left"),
                                ("Wales", (HX[wa].min() - 1.5, HY[wa].mean()), "right")):
            ax.text(x, y, txt, fontsize=8.5, color=MUT, family=MONO, ha=ha, va="center", path_effects=HALO)


def lqcol(v, lim=4.0):
    lv = np.clip(np.log2(v), -np.log2(lim), np.log2(lim))
    return CMAP(Normalize(-np.log2(lim), np.log2(lim))(lv))


def out(fig, name, page=True, blog=True, paper=True):
    if paper:
        fig.savefig(f"{PAPD}/f_{name}.pdf", facecolor=fig.get_facecolor())
    fig.savefig(f"{SCR}/{name}.png", dpi=220, facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1500, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=85, optimize=True)
    if blog:
        im.resize((1800, round(im.size[1] * 1800 / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def title(fig, t, sub, y=0.965):
    fig.text(0.04, y, t, fontsize=21, fontweight="bold", family=DISP, color=INK, va="top")
    fig.text(0.04, y - 0.05, sub, fontsize=12, color=MUT, va="top")


def foot(fig, s=SRC):
    fig.text(0.04, 0.012, s, fontsize=8.3, family=MONO, color=MUT, va="bottom", linespacing=1.4)


def colorbar(fig, rect, lim=4, label="Signatures against the seat's usual share"):
    cax = fig.add_axes(rect)
    g = np.linspace(-np.log2(lim), np.log2(lim), 256)
    cax.imshow(g[None, :], cmap=CMAP, aspect="auto", extent=(g[0], g[-1], 0, 1))
    t = [-np.log2(lim), -1, 0, 1, np.log2(lim)]
    cax.set_xticks(t); cax.set_xticklabels([f"1/{lim:g}" if v < -1 else "half" if v == -1 else "usual" if v == 0 else "2x" if v == 1 else f"{lim:g}x+" for v in t], fontsize=9, family=MONO)
    cax.set_yticks([]); cax.set_title(label, fontsize=9.5, color=MUT, loc="left")
    for s in cax.spines.values(): s.set_visible(False)


def short(a, n=46):
    return a if len(a) <= n else a[:n - 1].rsplit(" ", 1)[0] + "..."


# ---------- 1. six petitions, six maps
CASES = [(711355, "local cause"), (700138, "rural"), (700005, "cities and campuses"), (737105, "coast and towns"), (700036, "moors and cities"), (700143, "everywhere, a little")]
fig = plt.figure(figsize=(12, 11.2))
title(fig, "Six petitions, six maps", "Each hex is a 2024 constituency. Red: the seat signed more than its usual share of all petition signatures; blue: less.")
for k, (p, tag) in enumerate(CASES):
    ax = fig.add_axes([0.03 + (k % 3) * 0.32, 0.50 - (k // 3) * 0.38, 0.30, 0.31])
    j = pids.index(p)
    hexmap(ax, lqcol(EB[:, j]), labels=False)
    c = R["cases"][str(p)]
    ax.set_title(short(P.action[p], 44) + f"\n{c['n']:,} signatures; {c['D_pc']:.0f}% would have to move", fontsize=10.2, color=INK, loc="left")
colorbar(fig, [0.33, 0.085, 0.34, 0.016])
foot(fig)
out(fig, "cases")

# ---------- 2. most over-signed petition family per seat (the map's default layer)
fig = plt.figure(figsize=(10, 11))
title(fig, "What each seat signs most", "For each 2024 constituency, the petition (of 10,000+ signatures) it over-signed most, coloured by topic")
ax = fig.add_axes([0.02, 0.07, 0.62, 0.82])
fams = PR.top_family.values
hexmap(ax, [FAMILY_COL[f] for f in fams])
lax = fig.add_axes([0.64, 0.25, 0.34, 0.6]); lax.axis("off")
cnt = pd.Series(fams).value_counts()
for i, f in enumerate([f for f in FAMILIES if f in cnt.index]):
    lax.add_patch(plt.Rectangle((0, 1 - i * 0.065 - 0.04), 0.07, 0.045, color=FAMILY_COL[f], transform=lax.transAxes))
    lax.text(0.1, 1 - i * 0.065 - 0.018, f"{FAMILY_NAME[f]} ({cnt[f]})", fontsize=10.5, va="center", transform=lax.transAxes)
lax.text(0, 1.03, "Topic of the top petition (seats)", fontsize=10.5, color=MUT, transform=lax.transAxes)
foot(fig)
out(fig, "top")

# ---------- 3. concentration by topic family
H2 = R["H2"]["fam"]
order = sorted(FAMILIES, key=lambda f: H2[f]["median_D_pc"])
fig = plt.figure(figsize=(11, 7.4))
title(fig, "Local causes are the most lopsided", "Share of a petition's signatures that would have to move for it to match the overall map of petition signing")
ax = fig.add_axes([0.30, 0.16, 0.65, 0.67])
for i, f in enumerate(order):
    v = 100 * PM.D[PM.family == f].values
    ax.scatter(v, np.full(len(v), i) + np.random.default_rng(1).uniform(-0.18, 0.18, len(v)), s=9, color=FAMILY_COL[f], alpha=0.45, lw=0)
    ax.plot([H2[f]["median_D_pc"]] * 2, [i - 0.32, i + 0.32], color=INK, lw=2.2)
ax.set_yticks(range(len(order))); ax.set_yticklabels([f"{FAMILY_NAME[f]} ({H2[f]['n']})" for f in order], fontsize=10.5)
ax.set_xlabel("Signatures that would have to move to match the overall map (%)"); ax.set_xlim(0, 100)
ax.grid(axis="x", color=RULE, lw=0.6); ax.set_axisbelow(True)
ax.text(H2["local"]["median_D_pc"] + 2, len(order) - 1 + 0.38, f"median {H2['local']['median_D_pc']:.0f}%", fontsize=9.5, color=INK, family=MONO)
fig.text(0.30, 0.85, "Dots: petitions. Bars: medians. Number of petitions in brackets.", fontsize=10, color=MUT)
foot(fig)
out(fig, "family")

# ---------- 4. clustering and the duplicates check
fig = plt.figure(figsize=(12, 5.6))
title(fig, "Petition maps are clustered, and repeat petitions repeat their maps", "Left: Moran's I of each petition's map (0 = no clustering), against the same maps with seats shuffled. Right: map correlations")
ax = fig.add_axes([0.06, 0.2, 0.42, 0.58])
ax.hist(PM.moran_I, bins=40, color=RED, alpha=0.85, label=f"real maps (median {R['H1']['median_I']:.2f})")
ax.axvline(R["P1"]["moran_placebo"], color=BLUE, lw=2.2, ls="--"); ax.text(R["P1"]["moran_placebo"] + 0.02, ax.get_ylim()[1] * 0.92, "seats shuffled", color=BLUE, fontsize=10, path_effects=HALO)
ax.set_xlabel("Moran's I (neighbouring seats)"); ax.set_ylabel("Petitions"); ax.legend(frameon=False, fontsize=10, loc="upper right")
ax2 = fig.add_axes([0.56, 0.2, 0.40, 0.58])
LOGm = np.log(EB); C = np.corrcoef(LOGm.T)
rng = np.random.default_rng(3); fam = P.loc[pids].family.values
rnd = [C[a, b] for a, b in rng.integers(0, len(pids), (3000, 2)) if fam[a] != fam[b]]
import importlib.util
GROUPS = json.loads(open(f"{SCR}/groups.json").read()) if os.path.exists(f"{SCR}/groups.json") else None
ax2.hist(rnd, bins=40, color=GREY, alpha=0.8, density=True, label="random pairs, different topics")
ax2.axvline(R["P2"]["median_within"], color=RED, lw=2.4)
ax2.text(R["P2"]["median_within"] - 0.02, ax2.get_ylim()[1] * 0.9, f"repeat petitions:\nmedian r = {R['P2']['median_within']:.2f}", color=RED, fontsize=10, ha="right", path_effects=HALO)
ax2.set_xlabel("Correlation between two petitions' seat maps"); ax2.set_ylabel("Density"); ax2.legend(frameon=False, fontsize=10, loc="upper left")
foot(fig)
out(fig, "moran")

# ---------- 5. personalities: PC1 and PC2 maps
fig = plt.figure(figsize=(12, 8.6))
title(fig, "Two signature personalities", "Seat scores on the first two components of all 734 petition maps (red: high; blue: low)")
for k, (nm, lab_hi, lab_lo) in enumerate((("pc1", "graduate, younger, more diverse", "older, whiter, higher Reform UK vote"),
                                          ("pc2", "Labour-held, poorer health", "Conservative and Lib Dem, older"))):
    ax = fig.add_axes([0.02 + k * 0.49, 0.07, 0.47, 0.68])
    v = PR[nm].values
    hexmap(ax, CMAP(Normalize(-2.5, 2.5)(np.clip(v, -2.5, 2.5))), labels=(k == 0))
    pcv = R["H3"][f"pc{k + 1}_pc"]
    ax.set_title(f"Component {k + 1} ({pcv:.0f}% of the variation)\nred = {lab_hi}\nblue = {lab_lo}", fontsize=10.5, loc="left", color=INK)
foot(fig)
out(fig, "pca")

# ---------- 6. clusters
CL = R["H3"]["clusters"]
fig = plt.figure(figsize=(10, 10.6))
title(fig, f"{R['H3']['k']} kinds of seat", "Seats grouped by their whole petition profile (k-means on five components)")
ax = fig.add_axes([0.02, 0.07, 0.62, 0.82])
colmap = {v["id"]: v["col"] for v in CL.values()}
hexmap(ax, [colmap[int(c)] for c in PR.cluster.values])
lax = fig.add_axes([0.64, 0.3, 0.34, 0.55]); lax.axis("off")
for i, (k, v) in enumerate(CL.items()):
    y = 1 - i * 0.3
    lax.add_patch(plt.Rectangle((0, y - 0.05), 0.07, 0.05, color=v["col"], transform=lax.transAxes))
    lax.text(0.1, y - 0.025, f"{k} ({v['n']})", fontsize=11, va="center", transform=lax.transAxes, fontweight="bold")
    lax.text(0.1, y - 0.09, "over-signs: " + short(v["top"][0]["a"], 34) + "\n" + short(v["top"][1]["a"], 40), fontsize=8.8, va="top", transform=lax.transAxes, color=MUT)
foot(fig)
out(fig, "clusters")

# ---------- 7. votes: R2 distributions and coefficients
fig = plt.figure(figsize=(12.5, 6.6))
title(fig, "Census shares explain petition maps better than the vote", "Left: how much of each petition's seat map is explained. Right: change in topic signing per standard deviation (England and Wales)")
ax = fig.add_axes([0.06, 0.19, 0.38, 0.59])
d = pd.read_csv(f"{DATA}/petition_measures.csv")
for col, lab_, c in (("r2_region", "region only (GB)", GREY), ("r2_votes_ew", "2024 vote shares (E&W)", RED), ("r2_census", "census shares (E&W)", BLUE)):
    ax.hist(100 * d[col], bins=np.linspace(0, 100, 41), histtype="step", lw=2.2, color=c, label=f"{lab_}: median {100 * d[col].median():.0f}%")
ax.set_xlabel("Variance explained (R squared, %)"); ax.set_ylabel("Petitions"); ax.legend(frameon=False, fontsize=9.5)
ax2 = fig.add_axes([0.58, 0.19, 0.39, 0.59])
rows = [("Immigration (all)", R["H4b"]["immigration"]), ("  tighter rules", R["exploratory"]["restrict"]), ("  more open rules", R["exploratory"]["open"]),
        ("Brexit and EU (all)", R["H4b"]["eu"]), ("  rejoin the EU", R["exploratory"]["rejoin"]), ("Animals", R["H4b"]["animals"]), ("Environment", R["H4b"]["environment"])]
for i, (lab_, dd) in enumerate(rows):
    for off, t, c in ((-0.2, "ruk_pct", "#3C9FB4"), (0.0, "ld_pct", GOLD), (0.2, "degree", INK)):
        e = dd[t]; y = len(rows) - 1 - i + off
        ax2.plot([e["lo"], e["hi"]], [y, y], color=c, lw=2); ax2.plot(e["pc"], y, "o", color=c, ms=5.5)
ax2.axvline(0, color=MUT, lw=1)
ax2.set_yticks(range(len(rows))); ax2.set_yticklabels([r_[0] for r_ in rows][::-1], fontsize=10)
ax2.set_xlabel("% change in the topic's signing per standard deviation")
for c, l in (("#3C9FB4", "Reform UK share"), (GOLD, "Lib Dem share"), (INK, "degree share")):
    ax2.plot([], [], "o-", color=c, label=l)
ax2.legend(frameon=False, fontsize=9.5, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=3)
fig.text(0.58, 0.86, "Tighter, more open and rejoin groups are exploratory (added after the planned models).", fontsize=9, color=MUT)
foot(fig)
out(fig, "votes")

# ---------- 8. robustness of the directional terms
rb = R["robust"]
fig = plt.figure(figsize=(12, 9.2))
title(fig, "Which links survive the checks", "The four planned directional estimates in every check: dots with 95% intervals (filled: interval excludes zero)")
labels = {"immigration_ruk": "Immigration topic and Reform UK share", "eu_ruk": "EU topic and Reform UK share", "eu_ld": "EU topic and Lib Dem share", "eu_green": "EU topic and Green share"}
for k, (t, lab_) in enumerate(labels.items()):
    ax = fig.add_axes([0.17 + (k % 2) * 0.48, 0.55 - (k // 2) * 0.43, 0.32, 0.30])
    rows = rb[t]["rows"]; names = list(rows)
    for i, nm in enumerate(names):
        e = rows[nm]; sig = e["lo"] > 0 or e["hi"] < 0
        ax.plot([e["lo"], e["hi"]], [i, i], color=RED if sig else GREY, lw=1.6)
        ax.plot(e["pc"], i, "o", color=RED if sig else GREY, mfc=(RED if sig else PAPER), ms=4.5)
    ax.axvline(0, color=MUT, lw=1); ax.set_yticks(range(len(names))); ax.set_yticklabels([n.replace("_", " ") for n in names], fontsize=6.6)
    ax.set_title(f"{lab_}: {rb[t]['n_sig']} of {rb[t]['n_checks']} checks", fontsize=11, loc="left"); ax.invert_yaxis()
    ax.set_xlabel("% change per SD", fontsize=9)
foot(fig)
out(fig, "robust", blog=False)

# ---------- header 1200 x 630
fig = plt.figure(figsize=(12, 6.3))
ax = fig.add_axes([0.56, 0.02, 0.42, 0.96])
hexmap(ax, CMAP(Normalize(-2.5, 2.5)(np.clip(PR.pc1.values, -2.5, 2.5))), labels=False)
fig.text(0.05, 0.80, "What each\nconstituency signs", fontsize=44, fontweight="bold", family=DISP, color=INK, va="top", linespacing=1.0)
fig.text(0.05, 0.43, f"The geography of {R['sample']['petitions']} UK Parliament petitions\nacross 650 seats, {R['inputs']['first_year']} to {R['inputs']['last_year']}", fontsize=15, color=MUT, va="top")
fig.text(0.05, 0.22, "Red: seats that over-sign the petitions of graduate,\nyounger, diverse places. Blue: the opposite.", fontsize=11.5, color=INK, va="top")
fig.text(0.05, 0.06, "Dr Tristan Hotham · maps.tristanhotham.com/petition-places", fontsize=10, family=MONO, color=MUT)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=PAPER)
plt.close(fig)
assert Image.open(f"{ROOT}/header.png").size == (1200, 630)
print("figures done", sorted(os.listdir(IMG)), sorted(os.listdir(BLOG)))
