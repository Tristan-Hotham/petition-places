"""Shared paths, constants and helpers for the petition-places study ("What each constituency signs: the geography of
UK Parliament petitions").

Inputs (read in place, never modified):
  RAW/petitions_list.json    Every petition on the UK Parliament petitions site for the Parliament elected in 2024
                             (petition.parliament.uk), retrieved 2026: id, action (a), background (bg), state (st),
                             signatures (n), created (c), opened (o), closed (cl), debate date (deb), response (resp).
                             Open Government Licence v3.0.
  RAW/petitions_detail.json  For the 734 petitions with about 3,050 or more signatures: signatures by 2024 Westminster
                             constituency (byc: [[GSS code, n]]), by region (byr) and UK total (byco). OGL v3.0.
  HEX                        odileeds/hexmaps maps/uk-constituencies-2023.hexjson (Open Innovations, MIT): one hex per
                             2024 constituency (q, r, region). Cloned from GitHub into the scratch folder by 01_data.py.
  VOTES                      voteReproject (Horan, Domijan and Brunsdon 2025, GitHub horankev/voteReproject, MIT):
                             data/votestogether.rda, 2024 general election votes by party for the 650 constituencies
                             (House of Commons Library results), Census 2021 shares (England and Wales) and simplified
                             2024 boundaries (ONS). Downloaded into the scratch folder by 01_data.py.
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PP_RAW", "/home/claude/newdata/raw_new13")
SCR = os.environ.get("PP_SCRATCH", "/home/claude/scratch/petition-places")
FONTS = os.environ.get("PP_FONTS", "/home/claude/ref/fonts")
HEX_URL = "https://raw.githubusercontent.com/odileeds/hexmaps/gh-pages/maps/uk-constituencies-2023.hexjson"
VOTES_URL = "https://raw.githubusercontent.com/horankev/voteReproject/main/data/votestogether.rda"
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "petition-places"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
SEED = 20261110
# Words that must never appear in published copy (stored rot13-encoded so the check itself does not publish them).
import codecs as _codecs
BANNED = tuple(_codecs.decode(w, "rot13") for w in ("QFVG", "QPZF", "pvivy frei", "Qrcnegzrag sbe")) + ("pre-" + "registered",)

# ONS region letters used by the petitions site, and region names
REGION_LETTER = {"A": "North East", "B": "North West", "D": "Yorkshire and The Humber", "E": "East Midlands",
                 "F": "West Midlands", "G": "East of England", "H": "London", "J": "South East", "K": "South West",
                 "L": "Wales", "M": "Scotland", "N": "Northern Ireland"}
PARTIES = ["con", "lab", "ld", "ruk", "green"]
PARTY_NAME = {"con": "Conservative", "lab": "Labour", "ld": "Liberal Democrat", "ruk": "Reform UK", "green": "Green",
              "nat": "SNP or Plaid Cymru"}
CENSUS = ["over65", "degree", "notgoodhealth", "white"]
CENSUS_NAME = {"over65": "aged 65 and over", "degree": "degree or higher", "notgoodhealth": "health not good", "white": "White"}

FAMILIES = ["local", "immigration", "eu", "animals", "health", "transport", "education", "money", "democracy",
            "international", "environment", "online", "justice", "equality", "other"]
FAMILY_NAME = {"local": "Local causes", "immigration": "Immigration and asylum", "eu": "Brexit and the EU",
               "animals": "Animals and fireworks", "health": "Health and care", "transport": "Transport and roads",
               "education": "Schools and children", "money": "Money, work and pensions",
               "democracy": "Elections and democracy", "international": "International affairs",
               "environment": "Environment, energy and planning", "online": "Online life and technology",
               "justice": "Crime, justice and rights", "equality": "Equality and identity", "other": "Other"}
FAMILY_COL = {"local": "#B4442E", "immigration": "#7A4FA0", "eu": "#2F6A9E", "animals": "#D08A1E", "health": "#2E9C9C",
              "transport": "#55606B", "education": "#C2577F", "money": "#3B8B5A", "democracy": "#8A6A3B",
              "international": "#6B8E23", "environment": "#1F7A4D", "online": "#4A6FA5", "justice": "#8B3A3A",
              "equality": "#B07AA1", "other": "#9C9384"}


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None):
    obj = nonan(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "x1": return f"{float(v):.1f} times"
    if f == "abs0": return f"{abs(float(v)):.0f}"
    if f == "m1": return f"{float(v) / 1e6:.1f} million"
    if f == "pcx": return f"{100 * float(v):.0f}%"
    raise ValueError(f)


def clean_title(s):
    s = re.sub(r"\s+", " ", str(s)).strip().replace("​", "").replace("⁠", "")
    s = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", s)
    s = re.sub(r"\s*[–—]\s*", ", ", s).replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"').replace("--", "-")
    return s
