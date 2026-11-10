**Title:** [OC] What each UK constituency signs: 734 Parliament petitions mapped across all 650 seats. Every map is clustered, and two "signature personalities" explain 30% of the differences between seats

**Body:**

The UK Parliament petitions site counts every signature by constituency. I took the 734 petitions of the current Parliament with about 3,000+ signatures (30.3 million signatures) and compared each seat's share of each petition with its share of all petition signing.

- All 734 petition maps are spatially clustered: neighbouring seats sign alike.
- Local causes are the most lopsided: "Grant Cornwall nation status" was signed at 67x the usual rate in Truro and Falmouth.
- Two dimensions hold 30% of the variation between seats; the first runs from graduate, younger, diverse seats to older, whiter seats. Split the petitions by date and the seat scores correlate 0.96.
- 2024 vote shares explain a median 26% of a petition's map; in England and Wales, four census shares explain more (31% against 23% for the vote).

Interactive map (search any seat or petition): https://maps.tristanhotham.com/petition-places/

**Source comment:**

Data: UK Parliament petitions site (Open Government Licence v3.0); 2024 results, Census 2021 shares and boundaries via the voteReproject R package (MIT); hexagons by Open Innovations (MIT). Method: empirical Bayes location quotients, Moran's I, PCA, regressions with a plan written before the analysis. Tools: Python (pandas, statsmodels, scikit-learn, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/petition-places
