"""Step 5: data/results.json (every number quoted anywhere) and the page data (data/site.json, data/site_sig.json)."""
import numpy as np, pandas as pd
from common import *

O = jload(f"{DATA}/_models.json")
I = jload(f"{DATA}/_summary_inputs.json")
Z = np.load(f"{SCR}/mat.npz", allow_pickle=True)
M, EB = Z["M"], Z["EB"]; codes = list(Z["codes"]); pids = [int(x) for x in Z["pids"]]
P = pd.read_csv(f"{DATA}/petitions.csv").set_index("id")
PM = pd.read_csv(f"{DATA}/petition_measures.csv").set_index("id")
SE = pd.read_csv(f"{DATA}/seats.csv").set_index("code").loc[codes]
PR = pd.read_csv(f"{DATA}/seat_profiles.csv").set_index("code").loc[codes]
R = {}


def pc(d):
    return {"pc": d["pc"], "lo": d["pc_lo"], "hi": d["pc_hi"], "p": d["p"], "n": d["n"]}


R["inputs"] = {**I, "n_overrides": int((P.family != P.family_rule).sum()),
               "overrides_pc": 100 * float((P.family != P.family_rule).mean()), "n_seats": len(codes),
               "detail_share_pc": 100 * I["detail_share_of_all"], "seat_share_pc": 100 * I["seat_share_of_n_median"],
               "largest": int(P.n.max()), "n_over_100k": int((P.n >= 100000).sum()), "n_over_10k": int((P.n >= 10000).sum()),
               "first_year": I["first_created"][:4], "last_year": I["last_created"][:4]}
R["families"] = {f: {"name": FAMILY_NAME[f], "n": int((P.family == f).sum()), "signatures": int(P.n[P.family == f].sum())} for f in FAMILIES}
h1 = O["H1"]
R["H1"] = {k: v for k, v in h1.items()}
R["H1"]["median_D_pc"] = 100 * h1["median_D"]; R["H1"]["median_D_excess_pc"] = 100 * h1["median_D_excess"]
R["H1"]["median_top10_pc"] = 100 * h1["median_top10"]
R["H1"]["top10_even_pc"] = 100 * 10 / 650
h2 = O["H2"]
R["H2"] = {"local": pc(h2["local"]), "n_local": h2["n_local"], "strict": pc(h2["strict_rules"]), "strict_n_local": h2["strict_rules"]["n_local"],
           "n10k": pc(h2["n10k"]), "n10k_n_local": h2["n10k"]["n_local"], "pw": pc(h2["petition_weighted_D"]),
           "I_local": h2["I_local_median"], "I_national": h2["I_national_median"],
           "D_local_pc": 100 * h2["D_local_median"], "D_national_pc": 100 * h2["D_national_median"],
           "top10_local_pc": 100 * h2["top10_local_median"], "top10_national_pc": 100 * h2["top10_national_median"],
           "fam": {f: {"geo_pc": 100 * v["geo"], "lo_pc": 100 * v["lo"], "hi_pc": 100 * v["hi"], "n": v["n"], "median_D_pc": 100 * v["median_D"],
                       "median_I": v["median_I"], "median_top10_pc": 100 * v["median_top10"]} for f, v in h2["family_D_excess"].items()}}
nat = {f: R["H2"]["fam"][f]["median_D_pc"] for f in FAMILIES if f not in ("local", "other")}
R["H2"]["most_geo_national"] = max(nat, key=nat.get); R["H2"]["least_geo_national"] = min(nat, key=nat.get)
h3 = O["H3"]
R["H3"] = {"pc1_pc": 100 * h3["var"][0], "pc2_pc": 100 * h3["var"][1], "pc3_pc": 100 * h3["var"][2], "pc12_pc": 100 * h3["pc12"], "pc15_pc": 100 * h3["pc15"],
           "stab1": h3["stability"]["PC1"]["half_corr"], "stab2": h3["stability"]["PC2"]["half_corr"], "stab3": h3["stability"]["PC3"]["half_corr"],
           "split_date_year": h3["split_date"][:4], "n_early": h3["n_early"], "n_late": h3["n_late"], "k": h3["k"],
           "sil": h3["silhouette"][str(h3["k"])], "sil_all": h3["silhouette"],
           "corr": {k: {n: v["r"] for n, v in d.items()} for k, d in h3["corr"].items()},
           "corr_n": h3["corr"]["PC1"]["degree"]["n"]}
CL_NAME = {}
cl = h3["clusters"]
order = sorted(cl, key=lambda c: -cl[c]["n"])
for c in order:
    d = cl[c]
    if d["nations"].get("Scotland", 0) + d["nations"].get("Northern Ireland", 0) > d["n"] / 2:
        CL_NAME[c] = ("Scotland and Northern Ireland", "#2F6A9E")
    elif d["degree"] > 40:
        CL_NAME[c] = ("Diverse cities", "#B4442E")
    else:
        CL_NAME[c] = ("Towns, suburbs and countryside", "#C9A227")
R["H3"]["clusters"] = {CL_NAME[c][0]: {"n": cl[c]["n"], "col": CL_NAME[c][1], "id": int(c), "degree": cl[c]["degree"], "over65": cl[c]["over65"],
                                      "white": cl[c]["white"], "ruk": cl[c]["ruk_pct"], "lab": cl[c]["lab_pct"], "con": cl[c]["con_pct"],
                                      "nations": cl[c]["nations"], "london": cl[c]["regions"].get("London", 0), "typical": cl[c]["typical"],
                                      "top": [{"id": t["id"], "a": t["a"], "x": t["x"]} for t in cl[c]["top"][:6]]} for c in order}
assert len({v[0] for v in CL_NAME.values()}) == h3["k"]
R["H3"]["load"] = {k: {"pos": [{"id": x["id"], "a": x["a"], "l": x["l"]} for x in v["pos"][:8]],
                       "neg": [{"id": x["id"], "a": x["a"], "l": x["l"]} for x in v["neg"][:8]]} for k, v in h3["load"].items()}
h4 = O["H4a"]
R["H4a"] = {k: v for k, v in h4.items() if k not in ("by_family", "top_r2", "low_r2")}
for k in ("median_r2_votes", "median_r2_region", "median_r2_votes_region", "median_r2_census_ew", "median_r2_votes_ew", "median_r2_votes_census_ew",
          "placebo_median_r2", "share_r2_votes_over_half", "share_votes_beat_census", "q25", "q75"):
    R["H4a"][k + "_pc"] = 100 * h4[k]
R["H4a"]["top_r2"] = h4["top_r2"]; R["H4a"]["low_r2"] = h4["low_r2"]
R["H4a"]["by_family"] = {f: {"r2_pc": 100 * v["median_r2"], "r2c_pc": 100 * v["median_r2_census"]} for f, v in h4["by_family"].items()}
R["H4b"] = {f: {t: pc(O["H4b"][f][t]) for t in [f"{p}_pct" for p in PARTIES] + CENSUS} | {"r2_pc": 100 * O["H4b"][f]["r2"], "n": O["H4b"][f]["n"]} for f in FAMILIES}
# robustness of the directional terms
alt = O["H4b_alt"]; loo = O["H4b_loo"]
rob = {}
for term, sign in (("immigration_ruk", 1), ("eu_ruk", -1), ("eu_ld", 1), ("eu_green", 1)):
    rows = {nm: alt[nm][term] for nm in alt} | {f"drop {rg}": loo[rg][term] for rg in loo}
    sig = sum(1 for d in rows.values() if (d["pc_lo"] > 0 if sign > 0 else d["pc_hi"] < 0))
    rob[term] = {"n_checks": len(rows), "n_sig": sig, "min_pc": min(d["pc"] for d in rows.values()), "max_pc": max(d["pc"] for d in rows.values()),
                 "rows": {nm: pc(d) for nm, d in rows.items()}}
R["robust"] = rob
ex = O["exploratory"]
R["exploratory"] = {g: {t: pc(ex[g][t]) for t in [f"{p}_pct" for p in PARTIES] + CENSUS} | {"n_petitions": ex[g]["n_petitions"], "corr_ruk": ex[g]["corr_ruk"],
                                                                                         "signatures": ex[g]["signatures"], "r2_pc": 100 * ex[g]["r2"]} for g in ("restrict", "open", "rejoin")}
R["exploratory"]["corr_restrict_open"] = ex["corr_restrict_open"]
R["P1"] = O["P1"]; R["P2"] = O["P2"]
R["P2"]["share_within_above_q90_pc"] = 100 * O["P2"]["share_within_above_q90"]
R["top"] = O["top"]; R["top"]["same_as_raw_pc"] = 100 * O["top"]["same_as_raw"]
R["activity"] = O["activity"]

# cases (named in the text)
CASES = [711355, 762755, 701546, 764785, 769805, 725716, 700138, 750236, 700036, 700005, 737105, 700143, 700682, 715511, 730194, 702845]
seatname = SE.name.to_dict()
R["cases"] = {}
for p in CASES:
    j = pids.index(p); o = np.argsort(-EB[:, j])
    R["cases"][str(p)] = {"a": P.action[p], "n": int(P.n[p]), "family": P.family[p], "D_pc": 100 * PM.D[p], "I": PM.moran_I[p],
                          "top10_pc": 100 * PM.top10_share[p], "r2_votes_pc": 100 * PM.r2_votes[p], "best_party": PM.best_party[p], "best_r": PM.best_r[p],
                          "top": [{"seat": seatname[codes[i]], "lq": float(EB[i, j]), "sig": int(M[i, j])} for i in o[:4]],
                          "low": [{"seat": seatname[codes[i]], "lq": float(EB[i, j])} for i in o[::-1][:3]]}
# a few seat cases for the map text
SC = {}
for nm in ("Sheffield Hallam", "Cambridge", "Great Yarmouth", "Brighton Pavilion", "Clacton", "Bethnal Green and Stepney", "Orkney and Shetland", "Truro and Falmouth"):
    c = SE.index[SE.name == nm][0]
    i = codes.index(c); j = pids.index(int(PR.top_petition[c]))
    SC[nm] = {"top": P.action[int(PR.top_petition[c])], "lq": float(EB[i, j]), "sig": int(M[i, j]), "signatures": int(M[i].sum()),
              "cluster": [k for k, v in R["H3"]["clusters"].items() if v["id"] == int(PR.cluster[c])][0], "pc1": float(PR.pc1[c]), "pc2": float(PR.pc2[c])}
R["seat_cases"] = SC
R["sample"] = {"petitions": len(pids), "seats": len(codes), "seat_signatures": int(M.sum()), "gb": h4["n_gb"], "ew": h4["n_ew"]}
jsave(R, f"{DATA}/results.json", indent=1)

# ---------------- page data ----------------
seats = []
for i, c in enumerate(codes):
    s = SE.loc[c]; pr = PR.loc[c]
    o = np.argsort(-np.where((M[i] >= 30) & (M.sum(0) >= 10000), EB[i], -1))[:5]
    seats.append({"c": c, "n": s["name"], "rg": s.region, "q": int(s.q), "r": int(s.r), "s": int(M[i].sum()), "vv": int(s.valid_votes),
                  "w": s.winner, "v": {p: round(float(s[f"{p}_pct"]), 1) for p in PARTIES + ["nat"]},
                  "k": int(pr.cluster), "p1": round(float(pr.pc1), 2), "p2": round(float(pr.pc2), 2),
                  "t": [[pids[j], round(float(EB[i, j]), 2), int(M[i, j])] for j in o]})
pets = []
for j, p in enumerate(pids):
    pets.append({"id": p, "a": P.action[p], "f": P.family[p], "n": int(P.n[p]), "st": P.state[p], "y": P.created[p][:4],
                 "D": round(100 * float(PM.D[p]), 1), "I": round(float(PM.moran_I[p]), 2), "r2": round(100 * float(PM.r2_votes[p])),
                 "bp": PM.best_party[p], "br": round(float(PM.best_r[p]), 2), "al": round(float(PM.eb_alpha[p]), 3), "ts": int(M[:, j].sum())})
site = {"seats": seats, "pets": pets, "fam": {f: [FAMILY_NAME[f], FAMILY_COL[f]] for f in FAMILIES},
        "cl": {str(v["id"]): [k, v["col"]] for k, v in R["H3"]["clusters"].items()}, "party": PARTY_NAME, "T": int(M.sum()),
        "Tc": [int(x) for x in M.sum(1)]}
jsave(site, f"{DATA}/site.json")
jsave({"order": codes, "s": [[int(x) for x in M[:, j]] for j in range(len(pids))]}, f"{DATA}/site_sig.json")
print("results.json", os.path.getsize(f"{DATA}/results.json") // 1024, "KB; site", os.path.getsize(f"{DATA}/site.json") // 1024, "KB; sig", os.path.getsize(f"{DATA}/site_sig.json") // 1024, "KB")
print(json.dumps(R["robust"], indent=0)[:1500])
print({k: (v["n"], v["typical"][:3]) for k, v in R["H3"]["clusters"].items()})
print(json.dumps(SC, indent=0))
