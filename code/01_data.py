"""Step 1: inputs to clean tables.
- downloads the 2024 constituency hexjson (odileeds/hexmaps) and the voteReproject 2024 results file into the scratch folder
- data/seats.csv: 650 seats with name, region, nation, hex position, 2024 vote shares, Census 2021 shares, centroid
- data/seats.geojson: simplified 2024 boundaries (for contiguity and the page's geographic view)
- data/petitions.csv: the 734 petitions with seat data (plus summary counts of all 17,201)
- data/signatures_by_seat.csv.gz: petition x seat signatures (long, non-zero)
"""
import csv, subprocess, warnings
import numpy as np, pandas as pd
from shapely.geometry import Polygon, MultiPolygon, mapping
from common import *

warnings.filterwarnings("ignore")
hexf, rda = f"{SCR}/hex2024.hexjson", f"{SCR}/vt.rda"
for url, fn in ((HEX_URL, hexf), (VOTES_URL, rda)):
    if not os.path.exists(fn):
        subprocess.run(["curl", "-sSL", "-o", fn, url], check=True)

H = jload(hexf)["hexes"]
import rdata
d = rdata.conversion.SimpleConverter(default_encoding="utf8").convert(rdata.parser.parse_file(rda, extension="rda"))["votestogether"]
cols = [c for c in d.columns if c != "geometry"]
V = pd.DataFrame({str(c): d[c].values for c in cols})
V["con_code"] = V.con_code.astype(str)
geoms = {}
for code, g in zip(V.con_code, d["geometry"].values):
    polys = []
    for part in g:
        rings = [np.asarray(r, float) for r in part]
        polys.append(Polygon(rings[0], rings[1:]))
    mp = MultiPolygon(polys) if len(polys) > 1 else polys[0]
    if not mp.is_valid:
        mp = mp.buffer(0)
    geoms[code] = mp
assert set(V.con_code) == set(H), "hex and votes codes differ"

# petitions
L = {p["id"]: p for p in jload(f"{RAW}/petitions_list.json")}
D = jload(f"{RAW}/petitions_detail.json")
rows, sig = [], []
for k, det in D.items():
    p = L[int(k)]
    byc = {c: int(v) for c, v in det["byc"]}
    assert set(byc) <= set(H), k
    rows.append({"id": p["id"], "action": clean_title(p["a"]), "state": p["st"],
                 "n": p["n"], "n_uk": int(det["byco"]), "n_seats": sum(byc.values()), "seats_with_any": len(byc),
                 "created": p["c"][:10], "opened": (p.get("o") or "")[:10], "closed": (p.get("cl") or "")[:10],
                 "debated": (p.get("deb") or "")[:10], "response": int(bool(p.get("resp")))})
    for c, v in byc.items():
        if v > 0:
            sig.append((p["id"], c, v))
P = pd.DataFrame(rows).sort_values("n", ascending=False)
P.to_csv(f"{DATA}/petitions.csv", index=False)
S = pd.DataFrame(sig, columns=["petition_id", "seat_code", "signatures"]).sort_values(["petition_id", "seat_code"])
S.to_csv(f"{DATA}/signatures_by_seat.csv.gz", index=False, compression="gzip")

# seats
reg = {v: k for k, v in REGION_LETTER.items()}
seat = []
tot = S.groupby("seat_code").signatures.sum()
for _, v in V.iterrows():
    c = v.con_code; h = H[c]; g = geoms[c]
    nation = {"E": "England", "W": "Wales", "S": "Scotland", "N": "Northern Ireland"}[c[0]]
    rp = g.representative_point()
    r = {"code": c, "name": h["n"], "region": v.region_name, "nation": nation, "q": h["q"], "r": h["r"],
         "lon": round(rp.x, 4), "lat": round(rp.y, 4), "valid_votes": int(v.valid_votes24), "winner": v.first_party24,
         "signatures": int(tot.get(c, 0))}
    for pty in PARTIES + ["snp", "pc", "dup", "sf", "sdlp", "uup", "apni", "other"]:
        r[f"{pty}_pct"] = round(float(v[f"{pty}24_pct"]), 3)
    r["nat_pct"] = round(r["snp_pct"] + r["pc_pct"], 3)
    for c2 in CENSUS:
        r[c2] = None if pd.isna(v[c2]) else round(float(v[c2]) * 100, 3)
    seat.append(r)
SE = pd.DataFrame(seat).sort_values("code")
assert len(SE) == 650 and SE.region.nunique() == 12, SE.region.unique()
SE.to_csv(f"{DATA}/seats.csv", index=False)

feats = []
for c in SE.code:
    g = geoms[c].simplify(0.0015, preserve_topology=True)
    m = mapping(g)
    def rnd(x):
        return [rnd(y) for y in x] if isinstance(x[0], (list, tuple)) else [round(x[0], 4), round(x[1], 4)]
    m = {"type": m["type"], "coordinates": rnd(m["coordinates"])}
    feats.append({"type": "Feature", "properties": {"code": c}, "geometry": m})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/seats.geojson")

# overall site counts (all 17,201)
A = pd.DataFrame([{"st": p["st"], "n": p["n"], "c": p["c"][:10]} for p in L.values()])
summary = {"all_petitions": len(A), "states": A.st.value_counts().to_dict(), "first_created": A.c.min(), "last_created": A.c.max(),
           "all_signatures": int(A.n.sum()), "detail_petitions": len(P), "detail_min_n": int(P.n.min()),
           "largest_not_detailed": int(A[~A.index.isin([])].pipe(lambda a: a[(a.n < P.n.min())].n.max())),
           "detail_signatures": int(P.n.sum()), "detail_seat_signatures": int(S.signatures.sum()),
           "seat_share_of_n_median": float((P.n_seats / P.n).median()), "detail_share_of_all": float(P.n.sum() / A.n.sum())}
jsave(summary, f"{DATA}/_summary_inputs.json", indent=1)
print(summary)
print("seats", len(SE), "petitions", len(P), "signature rows", len(S), "geojson KB", os.path.getsize(f"{DATA}/seats.geojson") // 1024)
