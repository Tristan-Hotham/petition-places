# petition-places: working notes

Brief: /home/claude/work/new13/BRIEFS.md section I (+ top of new12, new11, new10, new9, new8 briefs, house brief
/home/claude/newdata/BRIEF.md, GIF brief /home/claude/gifs/BRIEF.md). Format refs: byelection-attention, fame-half-life.
Scratch: /home/claude/scratch/petition-places (delete at the end, by exact path).

## Inputs (checked before any outcome analysis)

- /home/claude/newdata/raw_new13/petitions_list.json: 17,201 petitions of the current Parliament's petitions site
  (created 2024-10-30 to 2026-11-08): id, action, background, state (open 2,167, closed 5,977, rejected 9,057),
  signature count n, created/opened/closed dates, debate date, response flag, departments. The "topics" field is empty
  for every petition, so topic families must be coded from the text.
- petitions_detail.json: 734 petitions (every petition with about 3,050 or more signatures at retrieval: the smallest
  has 3,052, the largest not included 3,033); byc = signatures by 2024 Westminster constituency (GSS codes, 650 seats;
  seats with no signatures are absent), byr = by ONS region letter, byco = UK total. Sum of byc is a median 98.7% of n
  (the rest are signatures from abroad or without a matched postcode). Open Government Licence v3.0.
- 2024 constituency hexmap: odileeds/hexmaps maps/uk-constituencies-2023.hexjson (650 hexes, the 2023 boundary review
  seats used from 2024; all 650 codes match the petition data). Open Innovations, licence to be cited from the repo.
- 2024 general election results and seat outlines: voteReproject R package (Horan, Domijan and Brunsdon; GitHub
  horankev/voteReproject, MIT), data/votestogether.rda: 650 seats, 2024 votes and shares by party (from the House of
  Commons Library results), Census 2021 shares over 65, degree, not good health and white (England and Wales only, 575
  seats), and simplified 2024 boundary polygons (ONS, WGS84). Read with the Python package rdata (no R here).
- No 2024 electorates available from the shell. The 2023 review set every seat's electorate within 5% of the quota
  (69,724 to 77,062) except five protected seats, so raw seat totals are close to rates per elector; 2024 valid votes
  are used as an alternative denominator.

## Analysis plan (written 2026-11-10 08:40 UTC, before computing any seat-level petition measure)

Question. Where in the UK do people sign which Parliament petitions? Specifically: (Q1) how strongly does each petition's
geography depart from the overall map of petition signing, and does it cluster in space; (Q2) which topic families are
most and least geographic (local causes expected most); (Q3) do seats have stable "signature personalities" (a few
dimensions that summarise what a seat over-signs), and what do they look like; (Q4) how closely does petition interest
track the 2024 vote, compared with demographics and region.

Unit. Petition p by 2024 constituency c (734 x 650). Seat-level analyses use the 650 seats (GB 632 for party models;
England and Wales 575 where census controls are used).

Measures.
- S_pc signatures; T_c = sum over p (seat's total petition activity, the denominator required by the brief); T_p;
  T = grand total. Expected E_pc = T_p T_c / T. Location quotient LQ_pc = S_pc / E_pc.
- Main LQ: empirical Bayes shrunk LQ (Poisson-gamma, Clayton and Kaldor 1987): for each petition a gamma prior with mean
  1 and shape a_p estimated by the method of moments from the dispersion of raw LQs across seats; posterior mean
  (S_pc + a_p) / (E_pc + a_p). logLQ = log of this.
- Concentration of a petition: index of dissimilarity D_p = 0.5 sum_c |S_pc/T_p - T_c/T| (the share of its signatures
  that would have to move for it to match the overall map), and excess D = D_p minus its expectation under
  multinomial sampling with the same T_p (simulated, 50 draws). Also the share of signatures from the top 10 seats.
- Spatial clustering: Moran's I of logLQ on 2024 seat contiguity (simplified polygons, touching within ~200 m; seats
  with no land neighbour linked to their nearest seat; row-standardised), permutation p (199 permutations).
- Topic families (coded from the action and background text by ordered keyword rules in code/02_topics.py, every
  petition then read by eye and corrections kept in code/topic_overrides.csv): local causes (names a particular UK
  nation, region, county, town, route or site in the action: Cornwall, Northern Ireland veterans, London Mayor, a rail
  line...), immigration, Brexit and the EU, animals (incl. fireworks and slaughter labelling), health, transport,
  education and children, pensions/tax/welfare, elections and democracy, international affairs, environment and
  energy, online and technology, crime and justice, equality and identity, other.

Hypotheses and what would count against them.
- H1 (clustering). Petition geographies are spatially clustered: median Moran's I of logLQ > 0 and the majority of
  petitions significant at 5% by permutation. Against: median I near 0 or a minority significant.
- H2 (local causes). Local-cause petitions are more concentrated than national-topic petitions: OLS of log excess D
  (floor 0.005) on family dummies (reference: all national families pooled in the contrast) with log T_p and state
  (open/closed) as controls, HC3 errors; the local-minus-national contrast > 0. Against: CI including 0. Families
  other than local: two-sided, descriptive.
- H3 (personalities). Seat profiles have a low-dimensional structure that is stable over time. PCA of the seat x
  petition matrix of logLQ (columns standardised). Reported: variance share of PC1 to PC5; k-means clusters on PC1 to
  PC5 scores (k chosen by silhouette over 3 to 8, seed fixed). Stability: split petitions by creation date at the
  median; recompute the PCA in each half; correlation of seat scores on the matched components (sign aligned).
  Expect PC1 to PC2 together > 20% of variance and half-to-half correlation > 0.7 for PC1. Against: correlation < 0.5.
  Interpretation by correlation of scores with 2024 vote shares and census shares (descriptive).
- H4 (votes). Petition geography tracks the 2024 vote. (a) For each petition, OLS of logLQ on 2024 vote shares (Con,
  Lab, LD, Reform UK, Green, SNP plus Plaid) in GB seats: distribution of R2 (median and share above 0.5), compared
  with R2 from region fixed effects alone and (England and Wales) census shares alone. (b) Family level: seat family
  LQ (family signatures over expected) as outcome, logged; regressed on the five GB-wide party shares (SNP/PC absorbed
  by nation dummies) plus census controls and region fixed effects (England and Wales, 575), HC3 errors; directional
  expectations: immigration family positive on Reform UK share; EU family (rejoin petitions) negative on Reform UK and
  positive on Lib Dem/Green; all others two-sided. Standardised coefficients (per SD) with 95% CIs. Against: CI
  including 0 or opposite sign.
- Correlational only: seats are not people. No ecological claims about individual signers or voters.

Pre-specified checks.
- Placebo/falsification: (P1) Moran's I and vote R2 with seat labels permuted (expect about 0 and about the R2 of
  random regressors, 6/632); (P2) split-half reliability of each petition's logLQ map by random halves of its
  signers is not possible (no individual data), so instead: same-topic duplicates (petitions with near-identical
  actions, e.g. the general election and personal allowance petitions) should have highly correlated maps; different
  topics much less. Report correlations of duplicate pairs vs random pairs.
- Alternative specifications: raw LQ (seats with S_pc >= 20) instead of EB; denominator = petition-weighted activity
  (mean of the petition shares) instead of signature totals; denominator = 2024 valid votes; dropping the five largest
  petitions (over 700,000 signatures each) from T_c; petitions with n >= 10,000 only; k-nearest neighbours (k = 6)
  weights for Moran's I.
- Clustered errors: region clusters (12; t with G-1 df) as an alternative to HC3 for H4b.
- Leave-one-out: H4b dropping each region in turn; dropping London; England only.
- Topic rules: strict (keyword-only, no manual overrides) vs final.
- Most over-signed petition per seat (for the map): highest EB LQ among petitions with n >= 10,000 and S_pc >= 30; also
  reported raw. Descriptive.

What the data cannot show. Who signed (no individual data; one person can sign once per petition but the seat is from
a self-declared postcode), why, or whether signatures reflect organised campaigns. Petitions open at retrieval are
still collecting. Seats differ in internet use and age, and signing petitions is a minority activity.

## Log

- 01_data.py: inputs checked (above). seats.csv (650), seats.geojson (simplified 0.0015 deg), petitions.csv (734),
  signatures_by_seat.csv.gz (459,228 non-zero petition-seat cells; 30,338,613 signatures matched to seats).
- 02_topics.py: ordered keyword rules, then every one of the 734 petitions read by eye; 123 (16.8%) moved by hand
  (code/topic_overrides.csv): mostly group or community petitions caught by the "local" rule (Hong Kong BN(O),
  Ukrainians) moved to immigration, SEND petitions from health to schools, gender identity petitions to equality,
  ECHR petitions to crime/justice/rights, housing and planning to environment/planning. Final local causes: 10 petitions.
  All done before any outcome was computed.
- 03_measures.py, 04_models.py: planned models run once as written. Fixes made without looking at outcomes changing:
  the GB family model without census controls needed controls=False (census is England and Wales only).
- Exploratory (added after seeing H4b, labelled in the paper): the immigration family pools petitions for tighter and
  for more open rules (stance coded by hand from the titles: 20 restrictive, 33 more open, 1 ambiguous left out), and the EU
  family includes non-rejoin petitions (rejoin-only: 5 petitions). Re-run H4b on these groups.
- k-means: silhouette picked k = 3 (0.37); the third cluster is mostly Scotland and Northern Ireland, which partly
  reflects England-only petitions (school attendance, English bus passes). Reported as such.
- Results (planned): H1 supported (734/734 clustered, median I 0.48); H2 supported (local +189%, CI 71 to 389) but rests on 10
  petitions and is not significant among 10k+ petitions; H3 supported (PC1+PC2 30%, split-half r 0.96/0.96); H4a: vote R2
  median 26% (region 26%, census 31% in E&W); H4b: EU x Reform negative in 19/19 checks, EU x Green 18/19, EU x LD 15/19,
  immigration x Reform positive in main spec but only 10/19 checks (not robust; reverses without census controls).
- Petition background text is used only by the topic rules and not republished (one background names a government
  department; titles only in published data).

## References: verification (2026)
Verified online in this session (title, authors, year, venue, volume, pages, DOI from publisher or repository pages, abstract
read): Vidgen and Yasseri 2020; Leston-Bandeira 2019; Wright 2016; Wright 2012; Hagen et al. 2016; Yasseri, Hale and Margetts
2017 (DOI from the publisher URL); Asher et al. 2019; Bochel 2013 (DOI not shown on the repository page); Escher and Riehm 2017
(title, venue, volume, pages, DOI verified; author names from the search listing, not from the fetched page); Matthews 2021;
Clayton and Kaldor 1987 (volume, issue, first page and DOI verified; last page 681 not shown); Anselin 1995; Duncan and Duncan
1955; Becker, Fetzer and Novy 2017; Goodwin and Heath 2016; Schlozman, Verba and Brady 2010; Halupka 2014; Puschmann, Bastos
and Schmidt 2017; Jungherr and Juergens 2010 (record showed issue ambiguously; cited as 2(4)); Hale, Margetts and Yasseri 2013
(ACM WebSci proceedings, no pages shown); Margetts, John, Hale and Yasseri 2016; Riehm, Boehle and Lindner 2014.
Verified earlier for sibling studies (taken from their checked bibliographies): Agnew 1987; Moran 1950; Robinson 1950;
Johnston and Pattie 2006; Jennings and Stoker 2016; MacKinnon and White 1985; Cameron and Miller 2015; Hanretty, Lauderdale
and Vivyan 2017; Jones and Baumgartner 2005; Soroka and Wlezien 2010; Seabold and Perktold 2010.
Data/software: voteReproject DESCRIPTION and LICENSE read from GitHub; odileeds/hexmaps LICENSE read (MIT).
The shared web-search budget ran out before Rousseeuw (silhouettes) and Jolliffe and Cadima (PCA) could be verified, so they
are not cited. Reviewer: recheck Escher and Riehm authors, Clayton and Kaldor end page, Jungherr and Juergens issue.
