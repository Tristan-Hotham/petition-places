"""Step 4: the planned models (NOTES.md): H1 clustering, H2 local causes, H3 seat personalities (PCA, k-means, stability),
H4 votes (per-petition R2 and family regressions), placebos, alternative specifications and leave-one-out checks.
Writes data/_models.json (raw results; 05_results.py turns it into results.json), data/seat_profiles.csv,
data/family_lq.csv, data/models.csv."""
import warnings
import numpy as np, pandas as pd
import statsmodels.api as sm
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from common import *

warnings.filterwarnings("ignore")
rng = np.random.default_rng(SEED)
Z = np.load(f"{SCR}/mat.npz", allow_pickle=True)
M, E, EB, RAW, W, K6 = Z["M"], Z["E"], Z["EB"], Z["RAW"], Z["W"], Z["K6"]
codes, pids = list(Z["codes"]), [int(x) for x in Z["pids"]]
P = pd.read_csv(f"{DATA}/petitions.csv").set_index("id").loc[pids].reset_index()
PM = pd.read_csv(f"{DATA}/petition_measures.csv").set_index("id").loc[pids].reset_index()
SE = pd.read_csv(f"{DATA}/seats.csv").set_index("code").loc[codes].reset_index()
LOG = np.log(EB)
OUT = {}
MODELS = []


def ci(res, name, scale=1.0, label=""):
    b, se = res.params[name], res.bse[name]
    lo, hi = res.conf_int().loc[name]
    d = {"coef": b, "se": se, "lo": lo, "hi": hi, "p": res.pvalues[name], "n": int(res.nobs),
         "pc": 100 * (np.exp(b * scale) - 1), "pc_lo": 100 * (np.exp(lo * scale) - 1), "pc_hi": 100 * (np.exp(hi * scale) - 1)}
    MODELS.append({"model": label, "term": name, **{k: d[k] for k in ("coef", "se", "lo", "hi", "p", "n")}})
    return d


def lq_from(Mx, denom=None):
    Tp = Mx.sum(0); Tc = Mx.sum(1)
    w = Tc / Tc.sum() if denom is None else denom / denom.sum()
    Ex = np.outer(w, Tp)
    r = np.where(Ex > 0, Mx / np.maximum(Ex, 1e-12), np.nan)
    s2 = np.nansum(Ex * (r - 1) ** 2, 0) / Ex.sum(0) - 1 / Ex.mean(0)
    a = np.where(s2 > 1e-6, 1 / np.maximum(s2, 1e-6), 1e6)
    return Ex, (Mx + a) / (Ex + a)


def moran(Zm, Wm):
    Zc = Zm - Zm.mean(0)
    return (Zc * (Wm @ Zc)).sum(0) / (Zc ** 2).sum(0)


# ---------------- H1 clustering ----------------
OUT["H1"] = {"median_I": float(np.median(PM.moran_I)), "q25_I": float(PM.moran_I.quantile(.25)), "q75_I": float(PM.moran_I.quantile(.75)),
             "min_I": float(PM.moran_I.min()), "max_I": float(PM.moran_I.max()),
             "share_sig": float((PM.moran_p < 0.05).mean()), "n_sig": int((PM.moran_p < 0.05).sum()), "n": len(PM),
             "median_I_knn6": float(np.median(PM.moran_I_knn6)),
             "median_D": float(PM.D.median()), "median_D_excess": float(PM.D_excess.median()),
             "median_top10": float(PM.top10_share.median())}
# placebo: permuted seat labels
Ip = []
for k in range(20):
    Ip.append(np.median(moran(LOG[rng.permutation(len(codes))], W)))
OUT["H1"]["placebo_median_I"] = float(np.mean(Ip))
# alternative measures
OUT["H1"]["median_I_raw"] = float(np.median(moran(np.log((M + 0.5) / (E + 0.5)), W)))  # raw LQ (0.5 added to avoid log 0)

# ---------------- H2 local causes ----------------
PM["lex"] = np.log(np.maximum(PM.D_excess, 0.005)); PM["lTp"] = np.log(PM.seat_signatures); PM["open"] = (PM.state == "open").astype(int)
PM["local"] = (PM.family == "local").astype(int)
r2 = sm.OLS(PM.lex, sm.add_constant(PM[["local", "lTp", "open"]])).fit(cov_type="HC3")
OUT["H2"] = {"local": ci(r2, "local", label="H2 local vs national, log excess D"), "n_local": int(PM.local.sum()), "n": len(PM)}
fam = pd.get_dummies(PM.family).astype(float)[FAMILIES]
X = pd.concat([fam, PM[["lTp", "open"]] - PM[["lTp", "open"]].mean()], axis=1)
r2b = sm.OLS(PM.lex, X).fit(cov_type="HC3")
OUT["H2"]["family_D_excess"] = {f: {"geo": float(np.exp(r2b.params[f])), "lo": float(np.exp(r2b.conf_int().loc[f][0])),
                                     "hi": float(np.exp(r2b.conf_int().loc[f][1])), "n": int(fam[f].sum()),
                                     "median_D": float(PM.D[PM.family == f].median()),
                                     "median_I": float(PM.moran_I[PM.family == f].median()),
                                     "median_top10": float(PM.top10_share[PM.family == f].median())} for f in FAMILIES}
for f in FAMILIES:
    MODELS.append({"model": "H2 family means, log excess D", "term": f, "coef": r2b.params[f], "se": r2b.bse[f],
                   "lo": r2b.conf_int().loc[f][0], "hi": r2b.conf_int().loc[f][1], "p": r2b.pvalues[f], "n": int(r2b.nobs)})
# strict rules check
PM["local_rule"] = (PM.family_rule == "local").astype(int)
r2s = sm.OLS(PM.lex, sm.add_constant(PM[["local_rule", "lTp", "open"]])).fit(cov_type="HC3")
OUT["H2"]["strict_rules"] = ci(r2s, "local_rule", label="H2 strict rules")
OUT["H2"]["strict_rules"]["n_local"] = int(PM.local_rule.sum())
big = PM.seat_signatures >= 10000
r2t = sm.OLS(PM.lex[big], sm.add_constant(PM.loc[big, ["local", "lTp", "open"]])).fit(cov_type="HC3")
OUT["H2"]["n10k"] = ci(r2t, "local", label="H2 n>=10k"); OUT["H2"]["n10k"]["n_local"] = int(PM.local[big].sum())
# Moran's I by local (exploratory description)
OUT["H2"]["I_local_median"] = float(PM.moran_I[PM.local == 1].median()); OUT["H2"]["I_national_median"] = float(PM.moran_I[PM.local == 0].median())
OUT["H2"]["D_local_median"] = float(PM.D[PM.local == 1].median()); OUT["H2"]["D_national_median"] = float(PM.D[PM.local == 0].median())
OUT["H2"]["top10_local_median"] = float(PM.top10_share[PM.local == 1].median()); OUT["H2"]["top10_national_median"] = float(PM.top10_share[PM.local == 0].median())


# ---------------- H3 personalities ----------------
def pca(L):
    Zs = (L - L.mean(0)) / L.std(0)
    U, s, Vt = np.linalg.svd(Zs, full_matrices=False)
    var = s ** 2 / (s ** 2).sum()
    scores = U * s
    # sign: positive loading sum on Reform-correlated side is arbitrary; fix so that PC has positive corr with degree share later
    return scores, Vt, var


sc, Vt, var = pca(LOG)
OUT["H3"] = {"var": [float(v) for v in var[:10]], "pc12": float(var[:2].sum()), "pc15": float(var[:5].sum())}
# orient components: PC1 positive = higher degree share (England and Wales), PC2 positive = higher Reform UK share
ew = SE.degree.notna().values
for k, ref in ((0, SE.degree.values), (1, SE.ruk_pct.values), (2, SE.over65.values)):
    m = ~np.isnan(ref)
    if np.corrcoef(sc[m, k], ref[m])[0, 1] < 0:
        sc[:, k] *= -1; Vt[k] *= -1
# correlations with seat characteristics
chars = {"degree": SE.degree, "over65": SE.over65, "notgoodhealth": SE.notgoodhealth, "white": SE.white,
         "con": SE.con_pct, "lab": SE.lab_pct, "ld": SE.ld_pct, "ruk": SE.ruk_pct, "green": SE.green_pct, "nat": SE.nat_pct,
         "signatures_per_vote": SE.signatures / SE.valid_votes}
gb = (SE.nation != "Northern Ireland").values
OUT["H3"]["corr"] = {}
for k in range(5):
    OUT["H3"]["corr"][f"PC{k + 1}"] = {}
    for nm, v in chars.items():
        v = v.values.astype(float); m = ~np.isnan(v) & gb
        OUT["H3"]["corr"][f"PC{k + 1}"][nm] = {"r": float(np.corrcoef(sc[m, k], v[m])[0, 1]), "n": int(m.sum())}
# loadings: top petitions each way
OUT["H3"]["load"] = {}
for k in range(3):
    o = np.argsort(Vt[k])
    OUT["H3"]["load"][f"PC{k + 1}"] = {"pos": [{"id": pids[j], "a": P.action[j], "fam": P.family[j], "l": float(Vt[k, j])} for j in o[::-1][:12]],
                                       "neg": [{"id": pids[j], "a": P.action[j], "fam": P.family[j], "l": float(Vt[k, j])} for j in o[:12]]}
    # family mean loadings
    OUT["H3"]["load"][f"PC{k + 1}"]["fam"] = {f: float(Vt[k][P.family.values == f].mean()) for f in FAMILIES}
# stability over time: split by creation date at the median
med = P.created.median() if False else sorted(P.created)[len(P) // 2]
early = (P.created < med).values
scA, VA, varA = pca(LOG[:, early]); scB, VB, varB = pca(LOG[:, ~early])
stab = {}
for k in range(3):
    rs = [abs(np.corrcoef(sc[:, k], scA[:, j])[0, 1]) for j in range(5)]
    ja = int(np.argmax(rs))
    rs = [abs(np.corrcoef(sc[:, k], scB[:, j])[0, 1]) for j in range(5)]
    jb = int(np.argmax(rs))
    stab[f"PC{k + 1}"] = {"half_corr": float(abs(np.corrcoef(scA[:, ja], scB[:, jb])[0, 1])), "comp_a": ja + 1, "comp_b": jb + 1}
OUT["H3"]["stability"] = stab; OUT["H3"]["split_date"] = med; OUT["H3"]["n_early"] = int(early.sum()); OUT["H3"]["n_late"] = int((~early).sum())
# k-means on PC1..5 scores
S5 = sc[:, :5] / sc[:, :5].std(0) * np.sqrt(var[:5] / var[0])
sil = {}
for k in range(3, 9):
    km = KMeans(n_clusters=k, n_init=20, random_state=SEED).fit(S5)
    sil[k] = float(silhouette_score(S5, km.labels_))
kbest = max(sil, key=sil.get)
km = KMeans(n_clusters=kbest, n_init=50, random_state=SEED).fit(S5)
lab = km.labels_
OUT["H3"]["silhouette"] = sil; OUT["H3"]["k"] = kbest
# describe clusters
clus = {}
for c in range(kbest):
    m = lab == c
    top = np.argsort(-LOG[m].mean(0))[:8]
    d = {"n": int(m.sum()), "pc1": float(sc[m, 0].mean()), "pc2": float(sc[m, 1].mean()),
         "top": [{"id": pids[j], "a": P.action[j], "fam": P.family[j], "x": float(np.exp(LOG[m, j].mean()))} for j in top],
         "fam": {f: float(np.exp(LOG[m][:, P.family.values == f].mean())) for f in FAMILIES}}
    for nm in ("degree", "over65", "white", "con_pct", "lab_pct", "ld_pct", "ruk_pct", "green_pct", "nat_pct"):
        d[nm] = float(np.nanmean(SE[nm].values[m]))
    d["nations"] = SE.nation[m].value_counts().to_dict(); d["regions"] = SE.region[m].value_counts().head(4).to_dict()
    d["examples"] = SE.name[m].tolist()[:0]
    # most typical seats (closest to centre)
    dd = ((S5[m] - km.cluster_centers_[c]) ** 2).sum(1)
    d["typical"] = SE.name.values[m][np.argsort(dd)[:6]].tolist()
    clus[c] = d
OUT["H3"]["clusters"] = clus

# ---------------- H4 votes ----------------
gbi = np.where(gb)[0]
Xv = SE.loc[gb, [f"{p}_pct" for p in PARTIES] + ["nat_pct"]].values
Xv1 = sm.add_constant(Xv)
Rd = pd.get_dummies(SE.region[gb], drop_first=True).astype(float).values
Xr1 = sm.add_constant(Rd)
ewi = np.where(ew)[0]
Xc1 = sm.add_constant(SE.loc[ew, CENSUS].values)


def r2_all(Y, X1):
    beta, *_ = np.linalg.lstsq(X1, Y, rcond=None)
    res = Y - X1 @ beta
    return 1 - (res ** 2).sum(0) / ((Y - Y.mean(0)) ** 2).sum(0)


Yg = LOG[gbi]
R2v = r2_all(Yg, Xv1); R2r = r2_all(Yg, Xr1); R2vr = r2_all(Yg, np.c_[Xv1, Rd])
R2c = r2_all(LOG[ewi], Xc1)
R2v_ew = r2_all(LOG[ewi], sm.add_constant(SE.loc[ew, [f"{p}_pct" for p in PARTIES] + ["nat_pct"]].values))
R2vc = r2_all(LOG[ewi], sm.add_constant(SE.loc[ew, [f"{p}_pct" for p in PARTIES] + ["nat_pct"] + CENSUS].values))
perm = []
for k in range(20):
    perm.append(np.median(r2_all(Yg, sm.add_constant(Xv[rng.permutation(len(gbi))]))))
best = {}
for j in range(len(pids)):
    cs = {p: np.corrcoef(Yg[:, j], SE.loc[gb, f"{p}_pct"].values)[0, 1] for p in PARTIES}
    pb = max(cs, key=lambda p: abs(cs[p])); best[pids[j]] = (pb, float(cs[pb]))
PM["r2_votes"] = R2v; PM["r2_region"] = R2r; PM["r2_census"] = R2c; PM["r2_votes_ew"] = R2v_ew; PM["r2_votes_census"] = R2vc
PM["best_party"] = [best[p][0] for p in pids]; PM["best_r"] = [best[p][1] for p in pids]
OUT["H4a"] = {"median_r2_votes": float(np.median(R2v)), "share_r2_votes_over_half": float((R2v > 0.5).mean()), "n_over_half": int((R2v > 0.5).sum()),
              "q25": float(np.quantile(R2v, .25)), "q75": float(np.quantile(R2v, .75)),
              "median_r2_region": float(np.median(R2r)), "median_r2_votes_region": float(np.median(R2vr)),
              "median_r2_census_ew": float(np.median(R2c)), "median_r2_votes_ew": float(np.median(R2v_ew)),
              "median_r2_votes_census_ew": float(np.median(R2vc)),
              "placebo_median_r2": float(np.mean(perm)), "n_gb": int(gb.sum()), "n_ew": int(ew.sum()),
              "share_votes_beat_census": float((R2v_ew > R2c).mean()),
              "best_party_counts": PM.best_party.value_counts().to_dict(),
              "best_abs_r_over_half": int((PM.best_r.abs() > 0.5).sum()),
              "by_family": {f: {"median_r2": float(PM.r2_votes[PM.family == f].median()),
                                "median_r2_census": float(PM.r2_census[PM.family == f].median()),
                                "best": PM.best_party[PM.family == f].value_counts().to_dict()} for f in FAMILIES}}
# examples: the petitions whose map best and worst follows the vote, among n >= 50,000
bigp = PM[PM.seat_signatures >= 50000].sort_values("r2_votes")
OUT["H4a"]["top_r2"] = [{"id": int(r.id), "a": r.action, "r2": float(r.r2_votes), "party": r.best_party, "r": float(r.best_r)} for r in bigp.tail(8)[::-1].itertuples()]
OUT["H4a"]["low_r2"] = [{"id": int(r.id), "a": r.action, "r2": float(r.r2_votes), "party": r.best_party, "r": float(r.best_r)} for r in bigp.head(8).itertuples()]


# family LQ per seat
def family_lq(Mx, Ex, fams):
    out = {}
    for f in FAMILIES:
        m = fams == f
        out[f] = np.log(Mx[:, m].sum(1) / Ex[:, m].sum(1))
    return pd.DataFrame(out)


FL = family_lq(M, E, P.family.values)
FL.insert(0, "code", codes)
FL.round(5).to_csv(f"{DATA}/family_lq.csv", index=False)
REGS = [f"{p}_pct" for p in PARTIES]


def fam_reg(FLd, mask, label, cov="HC3", extra=None, drop_region=None, controls=True):
    d = SE.loc[mask].copy()
    if drop_region:
        keep = d.region != drop_region; d = d[keep]
    X = d[REGS + (CENSUS if controls else [])].copy()
    sd = X.std()
    X = (X - X.mean()) / X.std()
    Rf = pd.get_dummies(d.region, drop_first=True).astype(float)
    X = sm.add_constant(pd.concat([X, Rf], axis=1))
    res = {}
    for f in FAMILIES:
        y = FLd.loc[d.index, f]
        if cov == "cluster":
            r = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.region)[0]}, use_t=True)
        else:
            r = sm.OLS(y, X).fit(cov_type="HC3")
        res[f] = {t: ci(r, t, label=f"{label} | {f}") for t in REGS + (CENSUS if controls else [])}
        res[f]["r2"] = float(r.rsquared); res[f]["n"] = int(r.nobs)
    return res


FLi = FL.set_index(pd.Index(range(len(codes))))
SE.index = range(len(codes))
H4b = fam_reg(FLi, ew, "H4b main (E&W, census, region FE, HC3)")
OUT["H4b"] = H4b
OUT["H4b_cluster"] = fam_reg(FLi, ew, "H4b region-clustered", cov="cluster")
OUT["H4b_nocensus_gb"] = fam_reg(FLi, gb, "H4b GB, no census", controls=False)
OUT["H4b_england"] = fam_reg(FLi, ew & (SE.nation == "England").values, "H4b England only")
# leave one region out, for the directional terms
loo = {}
for rg in sorted(SE.region[ew].unique()):
    rr = fam_reg(FLi, ew, f"H4b drop {rg}", drop_region=rg)
    loo[rg] = {"immigration_ruk": rr["immigration"]["ruk_pct"], "eu_ruk": rr["eu"]["ruk_pct"], "eu_ld": rr["eu"]["ld_pct"], "eu_green": rr["eu"]["green_pct"]}
OUT["H4b_loo"] = loo
# alternative denominators and subsets
Tc = M.sum(1)
alt = {}
E_pw, EB_pw = lq_from(M, denom=(M / M.sum(0)).mean(1))
alt["petition_weighted"] = (M, E_pw)
E_vv, EB_vv = lq_from(M, denom=SE.valid_votes.values.astype(float))
alt["valid_votes"] = (M, E_vv)
top5 = np.argsort(-M.sum(0))[:5]
keep = np.setdiff1d(np.arange(len(pids)), top5)
E_x5, EB_x5 = lq_from(M[:, keep])
alt_fams = {"drop_top5": P.family.values[keep]}
alt["drop_top5"] = (M[:, keep], E_x5)
k10 = np.where(M.sum(0) >= 10000)[0]
E_10, EB_10 = lq_from(M[:, k10]); alt["n10k"] = (M[:, k10], E_10); alt_fams["n10k"] = P.family.values[k10]
alt_res = {}
for nm, (Mx, Ex) in alt.items():
    FLx = family_lq(Mx, Ex, alt_fams.get(nm, P.family.values)).set_index(pd.Index(range(len(codes))))
    rr = fam_reg(FLx, ew, f"H4b alt {nm}")
    alt_res[nm] = {"immigration_ruk": rr["immigration"]["ruk_pct"], "eu_ruk": rr["eu"]["ruk_pct"], "eu_ld": rr["eu"]["ld_pct"], "eu_green": rr["eu"]["green_pct"]}
FLs = family_lq(M, E, P.family_rule.values).set_index(pd.Index(range(len(codes))))
rr = fam_reg(FLs, ew, "H4b strict rules")
alt_res["strict_rules"] = {"immigration_ruk": rr["immigration"]["ruk_pct"], "eu_ruk": rr["eu"]["ruk_pct"], "eu_ld": rr["eu"]["ld_pct"], "eu_green": rr["eu"]["green_pct"]}
rr = OUT["H4b_cluster"]
alt_res["region_clustered"] = {"immigration_ruk": rr["immigration"]["ruk_pct"], "eu_ruk": rr["eu"]["ruk_pct"], "eu_ld": rr["eu"]["ld_pct"], "eu_green": rr["eu"]["green_pct"]}
rr = fam_reg(FLi, ew & (SE.region != "London").values, "H4b no London")
alt_res["no_london"] = {"immigration_ruk": rr["immigration"]["ruk_pct"], "eu_ruk": rr["eu"]["ruk_pct"], "eu_ld": rr["eu"]["ld_pct"], "eu_green": rr["eu"]["green_pct"]}
rr = OUT["H4b_england"]
alt_res["england_only"] = {"immigration_ruk": rr["immigration"]["ruk_pct"], "eu_ruk": rr["eu"]["ruk_pct"], "eu_ld": rr["eu"]["ld_pct"], "eu_green": rr["eu"]["green_pct"]}
rr = OUT["H4b_nocensus_gb"]
alt_res["gb_no_census"] = {"immigration_ruk": rr["immigration"]["ruk_pct"], "eu_ruk": rr["eu"]["ruk_pct"], "eu_ld": rr["eu"]["ld_pct"], "eu_green": rr["eu"]["green_pct"]}
OUT["H4b_alt"] = alt_res
# H1 under alternative denominators and raw LQ
OUT["H1"]["median_I_petition_weighted"] = float(np.median(moran(np.log(EB_pw), W)))
OUT["H1"]["median_I_valid_votes"] = float(np.median(moran(np.log(EB_vv), W)))
# H2 under alternative denominator (petition-weighted excess D not simulated; raw D used)
share_pw = (M / M.sum(0)).mean(1)
Dpw = 0.5 * np.abs(M / M.sum(0) - share_pw[:, None]).sum(0)
PM["lD_pw"] = np.log(Dpw)
r = sm.OLS(PM.lD_pw, sm.add_constant(PM[["local", "lTp", "open"]])).fit(cov_type="HC3")
OUT["H2"]["petition_weighted_D"] = ci(r, "local", label="H2 petition-weighted D (log)")

# ---------------- P2 duplicate petitions ----------------
GROUPS = {"general election": [700143, 727309, 750050, 771833, 702341, 760199],
          "personal allowance": [702844, 737513, 762815, 767590, 780979],
          "free TV licences": [754292, 700117, 728658], "1950s women pensions": [700765, 751929, 700076],
          "rejoin the EU": [700005, 749128, 726413, 771102, 700041], "state pension at 60": [700113, 728656, 755283],
          "quieter fireworks": [738192, 700049, 739674], "close the borders": [700824, 729482],
          "school term-time leave": [700047, 733300, 763857], "schools bill": [722377, 747448],
          "non-stun slaughter": [700557, 729708, 762116, 783423],
          "five-year settlement routes": [727360, 727372, 751443, 745599, 731835, 745684, 751580],
          "social media under 16": [700086, 710283], "digital ID": [730194, 745717, 767079, 734246],
          "security workers": [750121, 714242], "recognise Palestine": [727717, 700119], "motorcycle licences": [706650, 743810],
          "animal abuser register": [759783, 756424], "student loan interest": [756832, 782464, 760570],
          "water ownership": [762640, 757426, 700436], "proportional representation": [728017, 700109, 762149]}
pj = {p: j for j, p in enumerate(pids)}
C = np.corrcoef(LOG.T)
within = []
for g, ids in GROUPS.items():
    assert all(i in pj for i in ids), g
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            within.append(C[pj[ids[a]], pj[ids[b]]])
fams = P.family.values
rand = []
for _ in range(4000):
    a, b = rng.integers(0, len(pids), 2)
    if fams[a] != fams[b]:
        rand.append(C[a, b])
OUT["P2"] = {"n_groups": len(GROUPS), "n_pairs": len(within), "median_within": float(np.median(within)), "min_within": float(np.min(within)),
             "median_random": float(np.median(rand)), "q90_random": float(np.quantile(rand, .9)), "share_within_above_q90": float(np.mean(np.array(within) > np.quantile(rand, .9)))}
OUT["P1"] = {"moran_placebo": OUT["H1"]["placebo_median_I"], "r2_placebo": OUT["H4a"]["placebo_median_r2"]}

# ---------------- seat profiles and most over-signed petitions ----------------
elig = (M.sum(0) >= 10000)
LQm = np.where((M >= 30) & elig[None, :], EB, -np.inf)
LQraw = np.where((M >= 30) & elig[None, :], RAW, -np.inf)
prof = SE[["code", "name", "region", "nation"]].copy()
prof["signatures"] = M.sum(1).astype(int); prof["sig_per_vote"] = (M.sum(1) / SE.valid_votes).round(4)
for k in range(5):
    prof[f"pc{k + 1}"] = (sc[:, k] / sc[:, k].std()).round(4)
prof["cluster"] = lab
top1 = LQm.argmax(1)
prof["top_petition"] = [pids[j] for j in top1]; prof["top_lq"] = EB[np.arange(len(codes)), top1].round(3)
prof["top_sig"] = M[np.arange(len(codes)), top1].astype(int)
prof["top_raw_petition"] = [pids[j] for j in LQraw.argmax(1)]
prof["top_family"] = [P.family.values[j] for j in top1]
prof.to_csv(f"{DATA}/seat_profiles.csv", index=False)
OUT["top"] = {"n_distinct": int(prof.top_petition.nunique()), "same_as_raw": float((prof.top_petition == prof.top_raw_petition).mean()),
              "family_counts": prof.top_family.value_counts().to_dict(),
              "most_common": [{"id": int(i), "a": P.set_index("id").action[i], "seats": int(c)} for i, c in prof.top_petition.value_counts().head(10).items()]}
# activity
spv = M.sum(1) / SE.valid_votes.values
OUT["activity"] = {"median_per_vote": float(np.median(spv)), "max_per_vote": float(spv.max()), "min_per_vote": float(spv.min()),
                   "max_seat": SE.name[int(spv.argmax())], "min_seat": SE.name[int(spv.argmin())],
                   "corr": {nm: float(np.corrcoef(spv[ew], SE.loc[ew, nm].values)[0, 1]) for nm in CENSUS},
                   "by_nation": {n: float(np.median(spv[(SE.nation == n).values])) for n in SE.nation.unique()},
                   "max_signatures_seat": SE.name[int(M.sum(1).argmax())], "max_signatures": int(M.sum(1).max()),
                   "min_signatures_seat": SE.name[int(M.sum(1).argmin())], "min_signatures": int(M.sum(1).min())}
PM.drop(columns=["lex", "lTp", "open", "local", "local_rule", "lD_pw"]).round(5).to_csv(f"{DATA}/petition_measures.csv", index=False)
pd.DataFrame(MODELS).to_csv(f"{DATA}/models.csv", index=False)
np.savez_compressed(f"{SCR}/pca.npz", sc=sc, Vt=Vt, var=var, lab=lab)
jsave(OUT, f"{DATA}/_models.json", indent=1)
print(json.dumps({k: OUT[k] for k in ("H1", "P1", "P2")}, indent=1)[:3000])
print("H2", {k: (round(v["pc"], 1), round(v["pc_lo"], 1), round(v["pc_hi"], 1)) for k, v in OUT["H2"].items() if isinstance(v, dict) and "pc" in v})
print("H3 var", np.round(var[:6], 3), OUT["H3"]["stability"], "k", kbest, sil)
print("H4a", {k: v for k, v in OUT["H4a"].items() if not isinstance(v, (dict, list))})
for f in ("immigration", "eu", "animals", "local", "environment"):
    print(f, {t: (round(H4b[f][t]["pc"], 1), round(H4b[f][t]["pc_lo"], 1), round(H4b[f][t]["pc_hi"], 1)) for t in REGS + CENSUS}, round(H4b[f]["r2"], 2))

# ---------------- exploratory (added after the planned models; labelled as such) ----------------
# The immigration family pools petitions for tighter and for more open rules; the EU family includes non-rejoin petitions.
RESTRICT = [737105, 705383, 718406, 700824, 773633, 778453, 777752, 763401, 764402, 729231, 761984, 716399, 776310,
            703195, 729482, 705093, 767461, 726409, 714124, 702908]
OPENER = [727360, 775267, 727372, 751443, 707698, 764063, 717065, 717817, 781255, 770812, 701769, 701137, 754152, 745599,
          775310, 710061, 731835, 700067, 700991, 700037, 751580, 714914, 781114, 745684, 713909, 746363, 727356, 700776,
          780004, 710067, 751315, 700387, 751548]
REJOIN = [700005, 749128, 726413, 771102, 700041]
assert set(RESTRICT + OPENER) <= set(P.id[P.family == "immigration"]) and not set(RESTRICT) & set(OPENER)
grp = np.array(["restrict" if p in RESTRICT else "open" if p in OPENER else "rejoin" if p in REJOIN else "-" for p in pids])
EX = {}
FLx = pd.DataFrame({g: np.log(M[:, grp == g].sum(1) / E[:, grp == g].sum(1)) for g in ("restrict", "open", "rejoin")})
for g in ("restrict", "open", "rejoin"):
    d = SE.loc[ew]
    X = (d[REGS + CENSUS] - d[REGS + CENSUS].mean()) / d[REGS + CENSUS].std()
    X = sm.add_constant(pd.concat([X, pd.get_dummies(d.region, drop_first=True).astype(float)], axis=1))
    r = sm.OLS(FLx.loc[d.index, g], X).fit(cov_type="HC3")
    EX[g] = {t: ci(r, t, label=f"Exploratory {g}") for t in REGS + CENSUS}
    EX[g]["n_petitions"] = int((grp == g).sum()); EX[g]["r2"] = float(r.rsquared)
    EX[g]["corr_ruk"] = float(np.corrcoef(FLx.loc[gb, g], SE.ruk_pct[gb])[0, 1])
    EX[g]["signatures"] = int(M[:, grp == g].sum())
EX["corr_restrict_open"] = float(np.corrcoef(FLx.restrict, FLx.open)[0, 1])
OUT["exploratory"] = EX
FLx.insert(0, "code", codes); FLx.round(5).to_csv(f"{DATA}/stance_lq.csv", index=False)
pd.DataFrame(MODELS).to_csv(f"{DATA}/models.csv", index=False)
jsave(OUT, f"{DATA}/_models.json", indent=1)
for g in ("restrict", "open", "rejoin"):
    print(g, EX[g]["n_petitions"], round(EX[g]["corr_ruk"], 2), {t: (round(EX[g][t]["pc"], 1), round(EX[g][t]["pc_lo"], 1), round(EX[g][t]["pc_hi"], 1)) for t in REGS + CENSUS})
print("corr restrict-open", EX["corr_restrict_open"])
