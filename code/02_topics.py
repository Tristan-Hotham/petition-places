"""Step 2: topic families for the 734 petitions, from ordered keyword rules on the action text (then the background if the
action matches nothing), with hand corrections in code/topic_overrides.csv after reading every petition.
Output: data/petitions.csv gains family_rule (rules only) and family (final)."""
import pandas as pd
from common import *

# ordered: first match wins. Local causes first (a particular UK place), then the brief's named families.
RULES = [
    ("local", r"\bcornwall\b|\bcornish\b|london mayor|mayor of london|northern ireland veterans|scottish parliament|"
              r"bedford|cambridge rail|east west rail|north of england a1|\bchalk stream|independence referendums? in scotland|"
              r"\bjewish communities\b|azad kashmir|polish veterans|britons in spain|hong ?kong|\bbn\(?o\)?s?\b|"
              r"ukrainians?\b|moldovans|romanian into"),
    ("immigration", r"\bilr\b|indefinite leave|asylum|migrant|immigra|deport|\bvisa\b|visas\b|refugee|citizenship|"
                    r"borders?\b|settlement for|settled status|long residence|dependants|foreign criminals|foreign-born|"
                    r"undocumented|\bpublic funds\b|leave to remain|eta-free|international students"),
    ("eu", r"european union|\bthe eu\b|\brejoin|re-join|\beu\b|brexit|exiting the european|customs union"),
    ("animals", r"animal|\bdogs?\b|\bcats?\b|\bpets?\b|puppy|badger|greyhound|hunting|\bhunt\b|grouse|slaughter|"
                r"wildlife|hedgehog|squirrel|\bbirds?\b|\bhares?\b|firework|xl bull|\bvet\b|\bhorses?\b|"
                r"balloon|netting|\bmeat\b|cages and crates|catapult|plant-based"),
    ("health", r"\bnhs\b|cancer|screening|disease|syndrome|disorder|diabetes|\bhealth|maternity|midwi|nurs|"
               r"endometriosis|pregnan|ultrasound|mammogram|therap|treatment|medic|hospital|\bgp\b|gps\b|ataxia|"
               r"parkinson|\bsma\b|folic|coeliac|sickle|menopause|pmdd|ivf|fertility|vaccin|covid|cannabis|"
               r"dental|abortion|heartbeat|surrogacy|suicide|\bcamhs\b|mental|lipoedema|thyroid|\bnice\b|"
               r"physician|paramedic|ambulance|stem cell|car t|\bmnd\b|hyperemesis|arfid|adhd|autis|neurodiver|"
               r"\bpda\b|seizure|allerg|epidermolysis|cpr|death certification|hospice|palliative|carbon monoxide|"
               r"\bbv\b|caesarean|limb difference|tampons|sanitary|gynaecolog|menstrual|social care|puberty|cass review|"
               r"tirzepatide|mhra|transition using|transgender healthcare|ehcp|\bsend\b|\bsen\b"),
    ("transport", r"driv|\broads?\b|pothole|\bbus\b|buses|\brail\b|railway|motorcycl|motorhome|e-scooter|scooter|"
                  r"e-bike|airport|parking|vehicle|\bcars?\b|\bev\b|\bevs\b|speed limit|box junction|headlight|"
                  r"taxi|mileage|petrol|\bhgv\b|campervan|bus lanes|free bus travel|collisions with cats"),
    ("education", r"school|pupil|\bchildren|\bchild\b|teach|curriculum|education|gcse|student loan|tuition|early years|"
                  r"nurser|childcare|childminder|homework|young people|kinship|parental responsibility|"
                  r"care leavers|play centres|home educat|flexischool|ofsted|academy trust|students"),
    ("money", r"pension|\btax|allowance|\bvat\b|benefit|\bpip\b|\bdwp\b|universal credit|\buc\b|carer|waspi|1950s women|"
              r"wage|\bpay\b|salar|council tax|stamp duty|national insurance|\bnic\b|inheritance|interest|"
              r"winter fuel|tv licen[cs]e|licence fee|motability|bereavement|cost|ground rent|leasehold|"
              r"service charge|rent|landlord|mortgage|park home|business rates|hmrc|making tax digital|cash payments|"
              r"overtime|christmas bonus|retirement|redundanc|job listings|hospitality|pubs\b|steel|ceramics|"
              r"blockchain|co-operatives|working temperature|right to buy|housebuilding|house building|house"),
    ("democracy", r"general election|election|referendum|parliament|\bmps?\b|by-elections|proportional representation|"
                  r"electoral|vote|voting|no confidence|manifesto|donations|recall|councillors|mayors|monarch|"
                  r"democracy|minister|bills? backed|political coverage|plurality|bbc|broadcast|news media|"
                  r"ofcom|freedom of speech|inquiry into (pro-israel|russian)|foreign influence|trades unions"),
    ("international", r"israel|gaza|palestin|ukraine|iran|chagos|syria|pakistan|india\b|china|\bus military|"
                      r"canzuk|balfour|overseas aid|international development|troops|defence and security pact|"
                      r"indigenous and tribal|montevideo|arms exports|military support"),
    ("environment", r"climate|net zero|sewage|water (industry|companies)|water a non|nationalise water|solar|wind farm|"
                    r"geo-?engineering|fossil|oil and gas|fracking|incinerat|landfill|\bco.? storage|nature|"
                    r"trees|river|green belt|grey belt|peat|planning|megasheds|data cent|bess|pollut|plastic|"
                    r"litter|food and drink that is safe|throwing away|edible food|disposable bbq|artificial grass|"
                    r"air quality|sustainab|15 minute|insulation|energy"),
    ("online", r"online|social media|digital id|identity cards|\bai\b|'ai'|generative|video games|internet|"
               r"misinformation|smart glasses|virtual private|vpn|dating apps|payment processors|data opt-out|"
               r"digital device|copyright|likeness|deepfake|tech manufacturers|edtech|telecoms|antennas|platforms"),
    ("justice", r"sentence|prison|offence|offender|crime|criminal|police|court|tribunal|knife|prosecut|murder|"
                r"terror|death penalty|whole life|jury|probation|bail|non-molestation|strangulation|"
                r"coercive|abuse|grooming|misogyny|hate|firearm|pepper spray|cctv|security worker|legal aid|"
                r"sex offender|child sexual|dbs|safeguard|bullying|disclosure|unfit to plead|unduly lenient|"
                r"emergency services|face coverings|face-coverings|full-face|nazi salute|religious exemptions|"
                r"misconduct|tenants don't pay|veterans|armed forces|military|cadet|service personnel"),
    ("equality", r"transgender|trans\b|gender|non-binary|lgbt|section 28|equality act|sex specific|sexed|"
                 r"woman and man|islamophobia|antisemitism|anti-palestinian|racism|anti-racism|disab|faith|"
                 r"bsl|sign language|wheelchair|changing benches|veteran"),
]


def classify(a, bg):
    for text in (a.lower(), bg.lower()):
        for fam, rx in RULES:
            if re.search(rx, text):
                return fam
    return "other"


P = pd.read_csv(f"{DATA}/petitions.csv")
BG = {p["id"]: clean_title(p.get("bg", "")) for p in jload(f"{RAW}/petitions_list.json")}  # background text used for rules only, not republished
P["family_rule"] = [classify(a, BG.get(i, "")) for a, i in zip(P.action, P.id)]
O = pd.read_csv(os.path.join(ROOT, "code", "topic_overrides.csv"), comment="#") if os.path.exists(os.path.join(ROOT, "code", "topic_overrides.csv")) else pd.DataFrame(columns=["id", "family", "why"])
assert set(O.family) <= set(FAMILIES), set(O.family) - set(FAMILIES)
ov = dict(zip(O.id, O.family))
assert set(ov) <= set(P.id), set(ov) - set(P.id)
P["family"] = [ov.get(i, f) for i, f in zip(P.id, P.family_rule)]
P.to_csv(f"{DATA}/petitions.csv", index=False)
print(P.family.value_counts().to_string())
print("overrides", len(ov), "changed", int((P.family != P.family_rule).sum()))
if os.environ.get("SHOW"):
    for fam in FAMILIES:
        print(f"\n## {fam}")
        for _, r in P[P.family == fam].iterrows():
            print(r.id, r.n, r.action[:100])
