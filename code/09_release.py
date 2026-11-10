"""Step 9: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo), README.md, LICENSE,
reddit/post.md and release/paper/cover_note.md, all filled from data/results.json. Run after 08_paper.py and reddit/collage.py.
10.5281/zenodo.24104518, https://doi.org/10.5281/zenodo.24104518 and https://blog.tristanhotham.com/2026/10/31/petition-places/ are left for the publisher to fill."""
import json as _json, shutil, zipfile, subprocess
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
NAME = "Hotham_Petition_Places"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
F = lambda p, f=None: fmt(get(R, p), f)
fill = lambda s: re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), s)
BAD = ("\u2014", "\u2013", "--") + BANNED


def clean(s, where):
    v = re.sub(r"<!--.*?-->", "", s, flags=re.S).replace("|---|---|", "")
    for b in BAD:
        assert b not in v, (where, b)


# ---------- blog
post = fill(open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read())
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8 and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
clean(post, "blog"); assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
meta = {"title": "What each constituency signs",
        "slug": "petition-places",
        "excerpt": f"I mapped {R['sample']['petitions']} UK Parliament petitions across all 650 constituencies. Every map is clustered, local causes are far more lopsided than other topics, and seats differ along two signature personalities that barely change over time.",
        "seo_description": f"Where in the UK do people sign which Parliament petitions? {R['sample']['petitions']} petitions mapped across all 650 constituencies.",
        "tags": ["maps", "data visualisation", "Parliament", "petitions", "constituencies", "political geography", "UK"],
        "header_alt": "Title card on cream paper reading 'What each constituency signs' beside a hexagon map of the 650 UK constituencies shaded from blue to red by their first signature personality."}
assert len(meta["seo_description"]) < 160
_json.dump(meta, open(f"{REL}/blog/meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", re.sub(r"<!--.*?-->", "", post, flags=re.S)).split())

# ---------- README, LICENSE, Reddit post, cover note
ex = R["exploratory"]
readme = f"""# What each constituency signs

The geography of UK Parliament petitions, {R['inputs']['first_year']} to {R['inputs']['last_year']}. The {R['sample']['petitions']} petitions to the Parliament elected in 2024 that had about 3,000 or more signatures, with their signatures counted in all 650 constituencies, compared seat by seat against each seat's overall petition signing, with hypotheses, measures and checks fixed in a written analysis plan before any outcome was computed (NOTES.md). A data study by Dr Tristan Hotham (Independent researcher).

Interactive page: {PAGE}
Paper: {{https://doi.org/10.5281/zenodo.24104518}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/petition-places/}}
Code and data: {REPO}

## Headline results

- Data: {R['sample']['petitions']} petitions with {R['inputs']['detail_signatures']:,} signatures ({F('inputs.detail_share_pc', 'f0')}% of all signatures on the site's {R['inputs']['all_petitions']:,} petitions), {R['sample']['seat_signatures']:,} of them assigned to the 650 seats.
- Clustering (H1): all {R['H1']['n_sig']} of {R['H1']['n']} petition maps are spatially clustered at 5% (median Moran's I {F('H1.median_I', 'f2')}; {F('P1.moran_placebo', 'f2')} with seats shuffled).
- Local causes (H2): median dissimilarity {F('H2.D_local_pc', 'f0')}% against {F('H2.D_national_pc', 'f0')}% for other petitions; excess dissimilarity {F('H2.local.pc', 'f0')}% higher (95% CI {F('H2.local.lo', 'f0')} to {F('H2.local.hi', 'f0')}), based on {R['H2']['n_local']} local petitions; not significant among petitions with 10,000+ signatures ({F('H2.n10k.pc', 'f0')}%, CI {F('H2.n10k.lo', 'f0')} to {F('H2.n10k.hi', 'f0')}).
- Signature personalities (H3): two principal components hold {F('H3.pc12_pc', 'f0')}% of the variation; PC1 correlates {F('H3.corr.PC1.degree', 'f2')} with the degree share and {F('H3.corr.PC1.ruk', 'f2')} with the 2024 Reform UK share. Split-half stability {F('H3.stab1', 'f2')} (PC1) and {F('H3.stab2', 'f2')} (PC2). Three seat groups by k-means (silhouette {F('H3.sil', 'f2')}).
- The vote (H4): 2024 vote shares explain a median {F('H4a.median_r2_votes_pc', 'f0')}% of a petition's map (GB), region alone {F('H4a.median_r2_region_pc', 'f0')}%; in England and Wales census shares {F('H4a.median_r2_census_ew_pc', 'f0')}% against the vote {F('H4a.median_r2_votes_ew_pc', 'f0')}%. EU petitions are under-signed where Reform UK polled well ({F('H4b.eu.ruk_pct.pc', 'f1')}% per SD, CI {F('H4b.eu.ruk_pct.lo', 'f1')} to {F('H4b.eu.ruk_pct.hi', 'f1')}; {R['robust']['eu_ruk']['n_sig']} of {R['robust']['eu_ruk']['n_checks']} checks). Immigration petitions and the Reform UK share: {F('H4b.immigration.ruk_pct.pc', 'f1')}% (CI {F('H4b.immigration.ruk_pct.lo', 'f1')} to {F('H4b.immigration.ruk_pct.hi', 'f1')}), significant in only {R['robust']['immigration_ruk']['n_sig']} of {R['robust']['immigration_ruk']['n_checks']} checks: not robust. Exploratory: petitions for tighter immigration rules and those to keep or open routes have opposite maps (correlation {F('exploratory.corr_restrict_open', 'f2')}).
- Reliability: near-identical petitions have similar maps (median r {F('P2.median_within', 'f2')} against {F('P2.median_random', 'f2')} for random pairs).

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre; hexagon and real-boundary views of the 650 seats; colour by top petition topic, any single petition (search), first signature personality, seat group, signing rate; layers panel, full screen, popups. |
| `header.png` | Social card, 1200 x 630. |
| `data/petitions.csv` | The {R['sample']['petitions']} petitions: title, state, signatures, dates, topic family (rules and final). |
| `data/signatures_by_seat.csv.gz` | Signatures by petition and 2024 constituency (non-zero cells). |
| `data/seats.csv`, `data/seats.geojson` | The 650 seats: hex position, region, 2024 vote shares, Census 2021 shares (England and Wales), simplified boundaries. |
| `data/petition_measures.csv` | Per petition: dissimilarity, excess dissimilarity, top-10 share, Moran's I and p, R squared from votes, region and census. |
| `data/seat_profiles.csv`, `data/family_lq.csv`, `data/stance_lq.csv` | Per seat: component scores, group, most over-signed petition; family and stance location quotients. |
| `data/models.csv`, `data/results.json` | Every model coefficient; every number quoted anywhere. |
| `data/site.json`, `data/site_sig.json`, `data/site_geo.json`, `data/weights.json` | Page data; contiguity weights. |
| `code/` | Scripts in order, templates, `topic_overrides.csv` (hand corrections), `qa.js`. |
| `release/` | Paper (PDF, LaTeX, figures, `cover_note.md`), blog post and figures, Zenodo files. |
| `reddit/` | Collage, its script, the looping GIF and the post text. |
| `NOTES.md` | Working notes and the analysis plan, written before the outcomes were computed. |

## Method in brief

- Location quotient: a seat's share of a petition's signatures against its share of all petition signatures, shrunk towards one with an empirical Bayes (Poisson-gamma) prior per petition.
- Concentration: index of dissimilarity, minus its multinomial expectation; clustering: Moran's I on seat contiguity with 199 permutations.
- Topics: ordered keyword rules, then every petition read by eye ({R['inputs']['n_overrides']} moved by hand).
- Personalities: PCA of the seat-by-petition matrix of log quotients; stability across petitions created before and after the median date; k-means on five components.
- Votes: per-petition R squared from 2024 vote shares, region and census shares; family regressions with census controls and region fixed effects (HC3), with 19 checks.

## How to rerun

Needs Python 3 with pandas, numpy, statsmodels, scikit-learn, shapely, rdata, matplotlib, Pillow; xelatex; node with Playwright for QA. Raw inputs are listed in `code/common.py`; the hexagon layout and the voteReproject file are downloaded from GitHub.

```
python3 code/01_data.py       # inputs to clean tables
python3 code/02_topics.py     # topic families
python3 code/03_measures.py   # location quotients, dissimilarity, Moran's I
python3 code/04_models.py     # planned models and checks, exploratory split
python3 code/05_results.py    # results.json and page data
python3 code/06_figures.py    # figures and header
python3 code/07_build_site.py # index.html
python3 code/08_paper.py      # paper (DOI=10.5281/zenodo.N to fill the DOI)
python3 reddit/collage.py
python3 code/09_release.py    # blog, Zenodo files, README, LICENSE, Reddit post, cover note
```

## Sources and licences

- UK Parliament petitions site, petition.parliament.uk: petitions and signatures by constituency, retrieved 2026. Contains public sector information licensed under the Open Government Licence v3.0.
- voteReproject (Horan, Domijan and Brunsdon 2025, MIT; https://github.com/horankev/voteReproject): 2024 general election results (House of Commons Library), Census 2021 shares and simplified 2024 boundaries (ONS, Open Government Licence).
- Hexagon layout: Open Innovations, odileeds/hexmaps (MIT).
- Base map: OpenFreeMap Positron (OpenStreetMap contributors, ODbL). MapLibre GL JS (BSD 3-Clause).
- Text, figures and derived data CC BY 4.0 (petition data also under the Open Government Licence v3.0); code MIT.

## Citation

Hotham, T. (2026) What each constituency signs: the geography of UK Parliament petitions, 2024 to 2026. Zenodo. {{https://doi.org/10.5281/zenodo.24104518}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
clean(readme, "readme")
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = """Code (code/, js/, reddit/collage.py): MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and the paper: Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/
Derived data (data/): CC BY 4.0. Petition counts contain public sector information licensed under the Open Government Licence v3.0 (UK Parliament petitions site). Vote and census shares and boundaries via voteReproject (MIT) from House of Commons Library and ONS data (Open Government Licence). Hexagon layout: Open Innovations (MIT).
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
c = R["cases"]
reddit = f"""**Title:** [OC] What each UK constituency signs: {R['sample']['petitions']} Parliament petitions mapped across all 650 seats. Every map is clustered, and two "signature personalities" explain {F('H3.pc12_pc', 'f0')}% of the differences between seats

**Body:**

The UK Parliament petitions site counts every signature by constituency. I took the {R['sample']['petitions']} petitions of the current Parliament with about 3,000+ signatures ({R['sample']['seat_signatures'] / 1e6:.1f} million signatures) and compared each seat's share of each petition with its share of all petition signing.

- All {R['H1']['n']} petition maps are spatially clustered: neighbouring seats sign alike.
- Local causes are the most lopsided: "{c['711355']['a']}" was signed at {c['711355']['top'][0]['lq']:.0f}x the usual rate in {c['711355']['top'][0]['seat']}.
- Two dimensions hold {F('H3.pc12_pc', 'f0')}% of the variation between seats; the first runs from graduate, younger, diverse seats to older, whiter seats. Split the petitions by date and the seat scores correlate {F('H3.stab1', 'f2')}.
- 2024 vote shares explain a median {F('H4a.median_r2_votes_pc', 'f0')}% of a petition's map; in England and Wales, four census shares explain more ({F('H4a.median_r2_census_ew_pc', 'f0')}% against {F('H4a.median_r2_votes_ew_pc', 'f0')}% for the vote).

Interactive map (search any seat or petition): {PAGE}

**Source comment:**

Data: UK Parliament petitions site (Open Government Licence v3.0); 2024 results, Census 2021 shares and boundaries via the voteReproject R package (MIT); hexagons by Open Innovations (MIT). Method: empirical Bayes location quotients, Moran's I, PCA, regressions with a plan written before the analysis. Tools: Python (pandas, statsmodels, scikit-learn, matplotlib), MapLibre. Paper and code: {REPO}
"""
clean(reddit, "reddit")
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(reddit)
txt = subprocess.run(["pdftotext", f"{REL}/paper/{NAME}.pdf", "-"], capture_output=True, text=True).stdout
pw = len(txt.split("References")[0].split()) if "References" in txt else len(txt.split())
cover = f"""# Cover note: What each constituency signs

## Suitable journals (word limits as checked for sibling papers in 2026; recheck before submitting)

The paper's main text is about {pw:,} words before the references (counted from the PDF, including tables and captions), with 8 figures and 7 tables (2 in the appendix).

1. **Political Geography** (Elsevier). Full-length papers up to 11,000 words; subscription publication is free to authors and open access is optional and paid (limit from the journal's listing as checked for a sibling study in 2026, not reconfirmed in this session). Fits as it stands. Best fit for the framing as a geography of revealed issue salience and its two stable dimensions.
2. **Parliamentary Affairs** (Oxford University Press, for the Hansard Society). Publishes the core e-petitions literature (Bochel 2013; Escher and Riehm 2017). Original articles at most 8,000 words and five figures and tables (OUP instructions as checked for a sibling study in 2026); a fee applies only for an open access licence. Fits on words; would need the exhibits cut to five, with the rest in an online appendix.
3. **British Journal of Politics and International Relations** (Sage, for the Political Studies Association). Published Matthews (2021) on MPs and e-petitions. Original articles 8,000 to 10,000 words excluding references, no fees for standard publication (checked for a sibling study in 2026). Fits as it stands.

Also considered: **Policy and Internet** (Wiley) publishes much of the e-petition literature but asks for 6,000 to 8,000 words including references, and its fee position was not confirmed; **The Journal of Legislative Studies** (Taylor and Francis) could not be checked from this workspace.

## Summary of the contribution (for a cover letter)

Research on e-petitions has asked who signs and whether petitions influence Parliament; this paper asks where they are signed. Using signature counts for all 650 constituencies on the {R['sample']['petitions']} petitions to the UK Parliament elected in 2024 that reached about 3,000 signatures, and an analysis plan written before any outcome was computed, it measures each petition's geography against each seat's overall signing with empirical Bayes location quotients. Every petition map is spatially clustered (median Moran's I {F('H1.median_I', 'f2')}); petitions about particular places are much more concentrated than national ones; and two dimensions, aligned with the education and age divides of recent British electoral geography, hold {F('H3.pc12_pc', 'f0')}% of the variation between seats and are almost identical across petitions created in different periods (r = {F('H3.stab1', 'f2')}). The 2024 vote explains about a quarter of a typical petition's map, less than census composition. EU petitions are robustly under-signed where Reform UK polled strongly; a planned link for immigration petitions is fragile because that family pools opposite aims. Data and code are openly released.
"""
clean(cover, "cover")
open(f"{REL}/paper/cover_note.md", "w", encoding="utf-8").write(cover)

# ---------- Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc", ".png")) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in ("petitions.csv", "signatures_by_seat.csv.gz", "seats.csv", "seats.geojson", "petition_measures.csv", "seat_profiles.csv",
               "family_lq.csv", "stance_lq.csv", "models.csv", "results.json", "weights.json"):
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(f"{REL}/paper/cover_note.md", f"{SLUG}/release/paper/cover_note.md")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$", "").replace("``", "\"").replace("''", "\"").replace("\\", "")
zmeta = {"title": "What Each Constituency Signs: The Geography of UK Parliament Petitions, 2024 to 2026",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/petition-places/}}.</p><p>Sources: UK Parliament petitions site (Open Government Licence v3.0); 2024 general election results, Census 2021 shares and simplified boundaries via voteReproject (MIT; House of Commons Library and ONS data); constituency hexagons by Open Innovations (MIT). Text, figures and data CC BY 4.0; code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["e-petitions", "political participation", "electoral geography", "constituencies", "spatial autocorrelation", "House of Commons", "United Kingdom"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
for b in BAD:
    assert b not in sj, b
_json.dump(zmeta, open(f"{Z}/metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip; paper words", pw)
