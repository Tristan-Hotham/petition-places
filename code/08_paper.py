"""Step 8: the paper. Fills code/paper_template.tex from data/results.json, adds the tables and compiles with xelatex.
Output: release/paper/Hotham_Petition_Places.pdf and .tex beside the f_*.pdf figures. The DOI is printed as the
placeholder https://doi.org/10.5281/zenodo.24104518 unless the environment variable DOI is set: DOI=10.5281/zenodo.N python3 code/08_paper.py"""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Petition_Places"


def tex(s):
    s = str(s)
    for a, b in (("\\", ""), ("&", "\\&"), ("%", "\\%"), ("_", "\\_"), ("#", "\\#"), ("$", "\\$"), ("£", "\\pounds{}")):
        s = s.replace(a, b)
    return s


def num(v, f):
    s = fmt(v, f)
    return s.replace("-", "$-$") if s.startswith("-") or " -" in s else s


def cell(d, k=1):
    return f"{d['pc']:.{k}f} [{d['lo']:.{k}f}, {d['hi']:.{k}f}]".replace("-", "$-$")


def star(d):
    s = f"{d['pc']:.1f}".replace("-", "$-$")
    return s + ("$^{*}$" if d["lo"] > 0 or d["hi"] < 0 else "")


fam = R["H2"]["fam"]
rows = ""
for f in sorted(FAMILIES, key=lambda f: -fam[f]["median_D_pc"]):
    v = fam[f]
    rows += (f"{tex(FAMILY_NAME[f])} & {v['n']} & {R['families'][f]['signatures'] / 1000:,.0f} & {v['median_D_pc']:.1f} & {v['median_I']:.2f} & "
             f"{v['median_top10_pc']:.1f} & {v['geo_pc']:.1f} [{v['lo_pc']:.0f}, {v['hi_pc']:.0f}]\\\\\n")
T_FAM = ("\\begin{table}[tbp]\\centering\\small\\caption{Topic families. $D$: index of dissimilarity (\\% of signatures that would have to move to match "
         "the overall map); $I$: Moran's $I$; top 10: share of signatures from the ten most over-signing seats; excess $D$: geometric mean of $D$ "
         "minus its sampling expectation, adjusted for log size and open status (model in Section~\\ref{sec:design}), with 95\\% CI. Medians unless stated.}\\label{tab:fam}"
         "\\footnotesize\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{lrrrrrl}\\toprule Family & $N$ & Sig. (000) & $D$ (\\%) & $I$ & Top 10 (\\%) & Excess $D$ (\\%)\\\\\\midrule\n"
         + rows + "\\bottomrule\\end{tabular}\\end{table}")
H2 = R["H2"]
T_H2 = ("\\begin{table}[tbp]\\centering\\small\\caption{H2: local causes against national petitions. OLS of log excess $D$ (floored at 0.005) on a local-cause indicator, "
        "log signatures and open status; HC3 errors. Entries: \\% difference for local causes with 95\\% CI.}\\label{tab:h2}"
        "\\begin{tabular}{lrrl}\\toprule Specification & Petitions & Local & Local vs national (\\%)\\\\\\midrule\n"
        f"Main (final coding) & {H2['local']['n']} & {H2['n_local']} & {cell(H2['local'], 0)}\\\\\n"
        f"Keyword rules only & {H2['strict']['n']} & {H2['strict_n_local']} & {cell(H2['strict'], 0)}\\\\\n"
        f"Petitions with 10,000+ signatures & {H2['n10k']['n']} & {H2['n10k_n_local']} & {cell(H2['n10k'], 0)}\\\\\n"
        f"Petition-weighted $D$ (log $D$) & {H2['pw']['n']} & {H2['n_local']} & {cell(H2['pw'], 0)}\\\\\n"
        "\\bottomrule\\end{tabular}\\end{table}")
H3 = R["H3"]; C = H3["corr"]
vars_ = [("degree", "Degree"), ("over65", "Aged 65+"), ("white", "White"), ("notgoodhealth", "Health not good"), ("con", "Conservative"),
         ("lab", "Labour"), ("ld", "Liberal Democrat"), ("ruk", "Reform UK"), ("green", "Green"), ("signatures_per_vote", "Signatures per vote")]
rows = f"Variance (\\%) & {H3['pc1_pc']:.1f} & {H3['pc2_pc']:.1f} & {H3['pc3_pc']:.1f}\\\\\nSplit-half $r$ & {H3['stab1']:.2f} & {H3['stab2']:.2f} & {H3['stab3']:.2f}\\\\\\midrule\n"
for k, lab in vars_:
    rows += f"{lab} & " + " & ".join(f"{C[p][k]:.2f}".replace("-", "$-$") for p in ("PC1", "PC2", "PC3")) + "\\\\\n"
T_PCA = ("\\begin{table}[tbp]\\centering\\small\\caption{H3: principal components of the seat-by-petition matrix of log location quotients. "
         f"Correlations of seat scores with census shares ($N$ = {H3['corr_n']} seats in England and Wales) and 2024 vote shares (Great Britain, $N$ = {R['sample']['gb']}). "
         "Components oriented so that PC1 correlates positively with the degree share and PC2 with the Reform UK share.}\\label{tab:pca}"
         "\\begin{tabular}{lrrr}\\toprule & PC1 & PC2 & PC3\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
A = R["H4a"]
T_R2 = ("\\begin{table}[tbp]\\centering\\small\\caption{H4a: median share of variance in a petition's seat map explained, across the "
        f"{R['sample']['petitions']} petitions.}}\\label{{tab:r2}}\\begin{{tabular}}{{llr}}\\toprule Predictors & Seats & Median $R^2$ (\\%)\\\\\\midrule\n"
        f"Region fixed effects & GB ({A['n_gb']}) & {A['median_r2_region_pc']:.1f}\\\\\n"
        f"2024 vote shares (six parties) & GB ({A['n_gb']}) & {A['median_r2_votes_pc']:.1f}\\\\\n"
        f"Vote shares and region & GB ({A['n_gb']}) & {A['median_r2_votes_region_pc']:.1f}\\\\\n"
        f"Vote shares, seats permuted (placebo) & GB ({A['n_gb']}) & {A['placebo_median_r2_pc']:.1f}\\\\\\midrule\n"
        f"Census shares (four) & E\\&W ({A['n_ew']}) & {A['median_r2_census_ew_pc']:.1f}\\\\\n"
        f"2024 vote shares & E\\&W ({A['n_ew']}) & {A['median_r2_votes_ew_pc']:.1f}\\\\\n"
        f"Vote and census shares & E\\&W ({A['n_ew']}) & {A['median_r2_votes_census_ew_pc']:.1f}\\\\\n"
        "\\bottomrule\\end{tabular}\\end{table}")
rb = R["robust"]
names = list(rb["eu_ruk"]["rows"])
lab = {"petition_weighted": "Petition-weighted denominator", "valid_votes": "Valid votes denominator", "drop_top5": "Five largest petitions dropped",
       "n10k": "Petitions with 10,000+ signatures", "strict_rules": "Keyword rules only", "region_clustered": "Region-clustered errors",
       "no_london": "London dropped", "england_only": "England only", "gb_no_census": "Great Britain, no census controls"}
rows = "Main specification & " + " & ".join(cell(R["H4b"][f][t]) for f, t in (("immigration", "ruk_pct"), ("eu", "ruk_pct"), ("eu", "ld_pct"), ("eu", "green_pct"))) + "\\\\\\midrule\n"
for nm in names:
    rows += f"{tex(lab.get(nm, nm.replace('drop ', 'Drop ')))} & " + " & ".join(cell(rb[t]["rows"][nm]) for t in ("immigration_ruk", "eu_ruk", "eu_ld", "eu_green")) + "\\\\\n"
rows += "\\midrule Checks with CI excluding 0 & " + " & ".join(f"{rb[t]['n_sig']} of {rb[t]['n_checks']}" for t in ("immigration_ruk", "eu_ruk", "eu_ld", "eu_green")) + "\\\\\n"
T_ROB = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Robustness of the four directional estimates (\\% change in family over-signing per SD, 95\\% CI). "
         "Main: England and Wales, census shares and region fixed effects, HC3 errors.}\\label{tab:rob}\\setlength{\\tabcolsep}{3pt}"
         "\\begin{tabular}{lllll}\\toprule Check & Immigration $\\times$ Reform UK & EU $\\times$ Reform UK & EU $\\times$ Lib Dem & EU $\\times$ Green\\\\\\midrule\n"
         + rows + "\\bottomrule\\end{tabular}\\end{table}")
TERMS = [("con_pct", "Con"), ("lab_pct", "Lab"), ("ld_pct", "LD"), ("ruk_pct", "Ref"), ("green_pct", "Grn"), ("over65", "65+"), ("degree", "Deg"), ("notgoodhealth", "Hlth"), ("white", "White")]
rows = ""
for f in FAMILIES:
    rows += f"{tex(FAMILY_NAME[f])} & " + " & ".join(star(R["H4b"][f][t]) for t, _ in TERMS) + f" & {R['H4b'][f]['r2_pc']:.0f}\\\\\n"
T_H4B = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{H4b: family over-signing on 2024 vote shares and census shares (England and Wales, "
         f"$N$ = {R['sample']['ew']} seats, region fixed effects, HC3). Entries: \\% change per SD; $^{{*}}$ 95\\% CI excludes zero. "
         "Con, Lab, LD, Ref, Grn: Conservative, Labour, Liberal Democrat, Reform UK and Green shares; 65+, Deg, Hlth, White: census shares aged 65 and over, "
         "degree or higher, health not good, White. Full estimates with standard errors are in data/models.csv.}\\label{tab:h4b}\\setlength{\\tabcolsep}{3pt}"
         "\\begin{tabular}{l" + "r" * (len(TERMS) + 1) + "}\\toprule Family & " + " & ".join(t for _, t in TERMS) + " & $R^2$ (\\%)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
EX = R["exploratory"]
rows = ""
for g, nm in (("restrict", "Immigration: tighter rules"), ("open", "Immigration: keep or open routes"), ("rejoin", "EU: rejoin")):
    rows += f"{nm} ({EX[g]['n_petitions']}) & " + " & ".join(star(EX[g][t]) for t, _ in TERMS) + f" & {EX[g]['r2_pc']:.0f}\\\\\n"
T_EX = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Exploratory (added after the planned models): the H4b model for immigration petitions split by stance "
        "and for the rejoin petitions alone. Number of petitions in brackets. Notation as in Table~\\ref{tab:h4b}.}\\label{tab:expl}\\setlength{\\tabcolsep}{3pt}"
        "\\begin{tabular}{l" + "r" * (len(TERMS) + 1) + "}\\toprule Group & " + " & ".join(t for _, t in TERMS) + " & $R^2$ (\\%)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k, v in (("TABLE_FAM", T_FAM), ("TABLE_H2", T_H2), ("TABLE_PCA", T_PCA), ("TABLE_R2", T_R2), ("TABLE_ROB", T_ROB), ("TABLE_H4B", T_H4B), ("TABLE_EXPL", T_EX)):
    t = t.replace(f"<<{k}>>", v)
doi = os.environ.get("DOI")
t = t.replace("<<DOIURL>>", f"\\url{{https://doi.org/{doi}}}" if doi else "\\{\\{DOI\\_URL\\}\\}")
t = t.replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO).replace("{{AI}}", AI)


def sub(m):
    v = get(R, m.group(1)); f = m.group(3)
    return tex(v) if isinstance(v, str) and f in (None, "raw") else num(v, f)


t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", sub, t)
assert "{{" not in t.replace("\\{\\{DOI\\_URL\\}\\}", ""), re.findall(r"\{\{[^}]*\}\}", t)[:5]
for bad in ("\u2014", "\u2013") + BANNED:
    assert bad not in t, bad
cites = set(re.findall(r"\\cite[tp]?\{([^}]+)\}", t)) | set(re.findall(r"\\citealt\{([^}]+)\}", t))
keys = {k.strip() for c in cites for k in c.split(",")}
bib = set(re.findall(r"\\bibitem\[[^\]]*\]\{([^}]+)\}", t))
print("references:", len(bib), "uncited:", sorted(bib - keys), "missing:", sorted(keys - bib))
assert not (keys - bib)
labels = set(re.findall(r"\\label\{([^}]+)\}", t)); refs = set(re.findall(r"\\ref\{([^}]+)\}", t))
assert {l for l in labels if l.startswith(("tab:", "fig:"))} <= refs, {l for l in labels if l.startswith(("tab:", "fig:"))} - refs
open(f"{OUT}/{NAME}.tex", "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", f"{NAME}.tex"], cwd=OUT, capture_output=True, text=True)
log = open(f"{OUT}/{NAME}.log", encoding="utf-8", errors="ignore").read()
assert os.path.exists(f"{OUT}/{NAME}.pdf"), r.stdout[-2000:]
print("undefined refs:", len(re.findall(r"undefined", log)), "overfull:", len(re.findall(r"Overfull \\hbox", log)))
for ext in ("aux", "log", "out"):
    if os.path.exists(f"{OUT}/{NAME}.{ext}"):
        os.remove(f"{OUT}/{NAME}.{ext}")
body = re.sub(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}", "", t, flags=re.S)
body = body.split("\\begin{document}")[1].split("\\appendix")[0]
words = len(re.sub(r"\\[a-zA-Z]+|[{}$\\]", " ", body).split())
pages = subprocess.run(["pdfinfo", f"{OUT}/{NAME}.pdf"], capture_output=True, text=True).stdout
print("words (main text incl. tables, excl. refs and appendix):", words, [l for l in pages.splitlines() if l.startswith("Pages")])
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", t, re.S).group(1)
print("abstract words:", len(ab.split()))
