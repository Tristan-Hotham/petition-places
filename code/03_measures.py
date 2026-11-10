"""Step 3: petition x seat measures (as fixed in the analysis plan, NOTES.md).
- expected counts E = T_p T_c / T, raw LQ, empirical Bayes LQ (Poisson-gamma, method of moments per petition)
- per petition: dissimilarity D, excess D over multinomial sampling, top-10-seat share, Moran's I of log EB LQ with a
  permutation p (contiguity weights), and Moran's I with 6-nearest-neighbour weights
- seat contiguity from data/seats.geojson
Outputs: data/_mat.npz (scratch-like cache inside data, deleted by 09_release), data/petition_measures.csv, data/weights.json
"""
import numpy as np, pandas as pd
from shapely.geometry import shape
from shapely.strtree import STRtree
from common import *

rng = np.random.default_rng(SEED)
P = pd.read_csv(f"{DATA}/petitions.csv")
SE = pd.read_csv(f"{DATA}/seats.csv").sort_values("code").reset_index(drop=True)
S = pd.read_csv(f"{DATA}/signatures_by_seat.csv.gz")
codes = SE.code.tolist(); ci = {c: i for i, c in enumerate(codes)}
pids = P.id.tolist(); pi = {p: j for j, p in enumerate(pids)}
M = np.zeros((len(codes), len(pids)))
M[S.seat_code.map(ci).values, S.petition_id.map(pi).values] = S.signatures.values


def lq_matrices(M, denom=None):
    """Expected counts and EB LQs. denom: seat weights (sums to 1) for the expected share; default T_c / T."""
    Tp = M.sum(0); Tc = M.sum(1)
    w = Tc / Tc.sum() if denom is None else denom / denom.sum()
    E = np.outer(w, Tp)
    raw = np.where(E > 0, M / np.maximum(E, 1e-12), np.nan)
    # method of moments for the gamma prior (mean 1): s2 = sum E (r-1)^2 / sum E - 1/mean(E)
    s2 = np.nansum(E * (raw - 1) ** 2, 0) / E.sum(0) - 1 / E.mean(0)
    alpha = np.where(s2 > 1e-6, 1 / np.maximum(s2, 1e-6), 1e6)
    eb = (M + alpha) / (E + alpha)
    return E, raw, eb, alpha


E, RAWLQ, EB, ALPHA = lq_matrices(M)
LOG = np.log(EB)

# weights: polygon contiguity (touching within about 250 m), islands linked to nearest seat
G = jload(f"{DATA}/seats.geojson")
geo = {f["properties"]["code"]: shape(f["geometry"]) for f in G["features"]}
polys = [geo[c].buffer(0.0025) for c in codes]
tree = STRtree(polys)
nb = {i: set() for i in range(len(codes))}
for i, p in enumerate(polys):
    for j in tree.query(p, predicate="intersects"):
        if j != i:
            nb[i].add(int(j)); nb[int(j)].add(i)
xy = np.c_[SE.lon.values * np.cos(np.radians(54)), SE.lat.values]
dist = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(-1)); np.fill_diagonal(dist, np.inf)
isolated = [codes[i] for i in nb if not nb[i]]
for i in nb:
    if not nb[i]:
        j = int(dist[i].argmin()); nb[i].add(j); nb[j].add(i)
W = np.zeros((len(codes), len(codes)))
for i, s in nb.items():
    for j in s:
        W[i, j] = 1
W = W / W.sum(1, keepdims=True)
K6 = np.zeros_like(W)
for i in range(len(codes)):
    K6[i, np.argsort(dist[i])[:6]] = 1 / 6
jsave({"codes": codes, "contig": {codes[i]: sorted(codes[j] for j in s) for i, s in nb.items()}, "isolated": isolated},
      f"{DATA}/weights.json")


def moran(Z, W):
    Zc = Z - Z.mean(0)
    return (Zc * (W @ Zc)).sum(0) / (Zc ** 2).sum(0)


I_c = moran(LOG, W); I_k = moran(LOG, K6)
NPERM = 199
Zc = LOG - LOG.mean(0); den = (Zc ** 2).sum(0)
ge = np.zeros(len(pids)); Iperm_med = []
for k in range(NPERM):
    Zp = Zc[rng.permutation(len(codes))]
    Ip = (Zp * (W @ Zp)).sum(0) / den
    ge += Ip >= I_c; Iperm_med.append(np.median(Ip))
pI = (ge + 1) / (NPERM + 1)

Tp = M.sum(0); Tc = M.sum(1); share_c = Tc / Tc.sum()
D = 0.5 * np.abs(M / Tp - share_c[:, None]).sum(0)
Dsim = np.zeros(len(pids))
for j in range(len(pids)):
    sims = rng.multinomial(int(Tp[j]), share_c, size=50)
    Dsim[j] = (0.5 * np.abs(sims / Tp[j] - share_c).sum(1)).mean()
top10 = np.sort(M / Tp, 0)[-10:].sum(0)
seat_top = [codes[i] for i in RAWLQ.argmax(0)]

out = P[["id", "action", "family", "family_rule", "n", "state", "created"]].copy()
out["seat_signatures"] = Tp.astype(int)
out["D"] = D.round(5); out["D_expected"] = Dsim.round(5); out["D_excess"] = (D - Dsim).round(5)
out["top10_share"] = top10.round(5)
out["moran_I"] = I_c.round(5); out["moran_p"] = pI.round(4); out["moran_I_knn6"] = I_k.round(5)
out["eb_alpha"] = ALPHA.round(3)
out["peak_seat"] = seat_top
out["peak_lq"] = np.nanmax(RAWLQ, 0).round(3)
out.to_csv(f"{DATA}/petition_measures.csv", index=False)
np.savez_compressed(f"{SCR}/mat.npz", M=M, E=E, EB=EB, RAW=RAWLQ, W=W, K6=K6, codes=np.array(codes), pids=np.array(pids))
print("isolated", isolated, "mean neighbours", np.mean([len(s) for s in nb.values()]))
print("median Moran I", np.median(I_c), "share p<.05", (pI < 0.05).mean(), "perm median I", np.median(Iperm_med))
print(out.groupby("family")[["D", "D_excess", "moran_I", "top10_share"]].median().sort_values("D_excess").round(3))
