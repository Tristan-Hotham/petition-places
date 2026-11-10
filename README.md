# What each constituency signs

The geography of UK Parliament petitions, 2024 to 2026. The 734 petitions to the Parliament elected in 2024 that had about 3,000 or more signatures, with their signatures counted in all 650 constituencies, compared seat by seat against each seat's overall petition signing, with hypotheses, measures and checks fixed in a written analysis plan before any outcome was computed (NOTES.md). A data study by Dr Tristan Hotham (Independent researcher).

Interactive page: https://maps.tristanhotham.com/petition-places/
Paper: {https://doi.org/10.5281/zenodo.24104518}
Blog post: {https://blog.tristanhotham.com/2026/10/31/petition-places/}
Code and data: https://github.com/Tristan-Hotham/petition-places

## Headline results

- Data: 734 petitions with 30,882,864 signatures (93% of all signatures on the site's 17,201 petitions), 30,338,613 of them assigned to the 650 seats.
- Clustering (H1): all 734 of 734 petition maps are spatially clustered at 5% (median Moran's I 0.48; -0.00 with seats shuffled).
- Local causes (H2): median dissimilarity 78% against 24% for other petitions; excess dissimilarity 189% higher (95% CI 71 to 389), based on 10 local petitions; not significant among petitions with 10,000+ signatures (110%, CI -5 to 365).
- Signature personalities (H3): two principal components hold 30% of the variation; PC1 correlates 0.79 with the degree share and -0.67 with the 2024 Reform UK share. Split-half stability 0.96 (PC1) and 0.96 (PC2). Three seat groups by k-means (silhouette 0.37).
- The vote (H4): 2024 vote shares explain a median 26% of a petition's map (GB), region alone 26%; in England and Wales census shares 31% against the vote 23%. EU petitions are under-signed where Reform UK polled well (-6.3% per SD, CI -9.3 to -3.1; 19 of 19 checks). Immigration petitions and the Reform UK share: 3.6% (CI 0.4 to 7.0), significant in only 10 of 19 checks: not robust. Exploratory: petitions for tighter immigration rules and those to keep or open routes have opposite maps (correlation -0.56).
- Reliability: near-identical petitions have similar maps (median r 0.63 against 0.01 for random pairs).

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre; hexagon and real-boundary views of the 650 seats; colour by top petition topic, any single petition (search), first signature personality, seat group, signing rate; layers panel, full screen, popups. |
| `header.png` | Social card, 1200 x 630. |
| `data/petitions.csv` | The 734 petitions: title, state, signatures, dates, topic family (rules and final). |
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
- Topics: ordered keyword rules, then every petition read by eye (123 moved by hand).
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

Hotham, T. (2026) What each constituency signs: the geography of UK Parliament petitions, 2024 to 2026. Zenodo. {https://doi.org/10.5281/zenodo.24104518}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
