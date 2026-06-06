# Tech & AI trade taxonomy — defined baskets and proposed extensions

This documents the HS6 product baskets used in the dashboard's **Tech & AI** tab, and proposes
how to handle the *increasingly borderline* categories around them. The organizing principle is
**proximity to the GPU**: the closer a product is to the compute silicon, the more cleanly it is
"AI/semiconductor"; the further out, the more **dual-use dilution** (the code also covers lots of
non-AI trade), so we tier rather than lump.

All codes are **HS6**. World export values are 2024 (HS2012 file, Atlas/Comtrade-derived). The
defined baskets (Tier A) are already in `src/gec/classifications.py` and shipped in
`dashboard/public/data/techai.json`; Tiers B–C are proposals.

---

## Tier A — Compute silicon (DEFINED, in the dashboard)

Two external, citable definitions. These are tight and well-motivated; we use them as-is.

### A1. Fed "AI compute" (finished AI hardware) — 3 codes
Source: Federal Reserve **FEDS Note, "The Global Trade Effects of the AI Infrastructure Boom"**
(2026-02-13). A deliberately narrow set (AI servers + accelerator cards); the authors note it can
both under- and over-count AI trade. World 2024 ≈ **$345B**.

| HS6 | description |
|---|---|
| 847150 | ADP processing units, n.e.s. (AI servers, e.g. NVIDIA DGX) |
| 847180 | Other ADP units (e.g. HGX baseboards) |
| 847330 | Parts/accessories of 8471 machines (e.g. GPU / accelerator cards) |

### A2. OECD semiconductor value chain — 59 codes, 6 stages
Source: **OECD (2025), "Mapping the semiconductor value chain"** (HS2017), via the Mexico
semiconductor-ecosystem report (doi:10.1787/4154cdbf-en). World 2024 ≈ **$1.3T**. Stages:

- **Chips** (finished ICs + discretes): `854110/121/129/130/160/190`, `854231/232/233/239/290`
  (processors, **memories**, amplifiers, other ICs, parts), `852351/352/359` (flash/smart cards/media),
  `853290/853390` (capacitor/resistor parts).
- **Photosensitive devices**: `854140`, `854150` (PV cells, LEDs, sensors).
- **Raw materials**: rare gases (`280421/429`), silicon `280461`, `281212`, germanium/gallium/indium
  (`282560`, `811292/299`), borates/silicon-carbide, etc.
- **Manufacturing equipment**: `848610/620/630/640/690` (wafer/IC/FPD/mask machines + parts),
  fans/heat-exchange/filtration (`841459`, `841950`, `8421xx`), metrology (`903082/084`, `903300`).
- **Foundry inputs** (optics/lithography): `9001xx`, `9002xx`, `901210/290`, `903141`.
- **Wafer inputs**: photographic plates/film/chemicals (`3701xx`, `370790`), **silicon wafers `381800`**.

**Coverage of Tier A:** raw inputs → fab/lithography equipment → chips → finished AI servers. This
is the *silicon* story and is well captured. What it omits is the **infrastructure that wraps the
chips inside a data center** — addressed below.

---

## Tier B — AI / data-center infrastructure (PROPOSED: high relevance, some dual-use)

The "rack around the GPU." Material and genuinely AI-driven, but the HS codes also carry non-AI
trade (telecom, general power, all electronics), so this should be a **separate, clearly-labeled
basket**, not merged into Tier A. Proposed group ≈ **$0.45T** world 2024.

| HS6 | description | world 2024 | AI relevance / caveat |
|---|---|---:|---|
| **851762** | network switching & routing apparatus | **$177.2B** | AI clusters are interconnect-bound; *also* all telecom/carrier routing |
| **850440** | static converters (PSU/UPS/rectifiers) | **$90.7B** | data-center power; dual-use (all electronics) |
| 851770 | parts of network/telephone apparatus | $85.0B | pairs with 851762 |
| 847170 | ADP storage units (HDD/SSD) | $50.7B | data-center storage; clean sibling of A1 |
| 853400 | bare printed circuit boards | $46.5B | substrates / advanced packaging — a real AI bottleneck |
| 853890 | parts for boards / switchgear | $35.0B | |
| 854470 | optical fibre cables (made up) | $8.8B | cluster optical interconnect; specific |
| 900110 | optical fibres / bundles | $2.2B | optical transceivers/DAC inputs |
| 850423 | liquid-dielectric transformers (large) | $8.8B | substation/DC power (optional) |
| 850434 | transformers > 500 kVA | $2.0B | substation/DC power (optional) |

**Suggested sub-structure** (mirrors the OECD stage idea):
- *Networking & interconnect*: 851762, 851769, 851770, 854470, 900110
- *Power*: 850440 (+ 850423, 850434 optional)
- *Storage*: 847170
- *Boards / substrates*: 853400, 853890

---

## Tier C — Adjacent / dual-use (DOCUMENTED: recommend exclude, or separate sensitivity set)

Material, but either a **different boom** or **too dual-use** to attribute to AI. Keep out of the
AI baskets; if shown at all, label as a broad "ICT/energy hardware" sensitivity set.

| HS6 | description | world 2024 | why it's Tier C |
|---|---|---:|---|
| 850760 | lithium-ion batteries | $101.6B | the **EV / energy-storage** boom, not AI compute |
| 854442 | insulated conductors w/ connectors | $36.8B | in everything electronic |
| 853669 | plugs & sockets / connectors | $21.8B | generic component |
| 841510 | air-conditioning (window/wall) | $21.6B | DC cooling, but mostly generic HVAC |
| 853224 | multilayer ceramic capacitors | $16.0B | generic passive (in all devices) |
| 841869 | refrigerating / freezing equipment | $12.5B | generic cooling |
| 847950 | industrial robots, n.e.c. | $5.7B | automation/tech, not AI-compute infra |
| 853221 | tantalum capacitors | $2.0B | generic passive |

---

## The tiering principle

| tier | layer | AI-specificity | dual-use dilution | dashboard |
|---|---|---|---|---|
| **A** | compute silicon (chips, fab, finished servers) | high | low | included |
| **B** | data-center infrastructure (network/power/storage/PCB/optical) | medium | medium | **proposed (separate basket)** |
| **C** | generic ICT / energy / passives | low | high | document only |

Moving A → C, two things rise together: the **dollar base** (851762 alone, $177B, dwarfs the whole
$345B Fed AI basket) and the **share of that base that has nothing to do with AI**. That trade-off
is the whole reason to tier: Tier B is worth showing as its own lens ("what fills a data center
besides the chips"), but folding it into the OECD/Fed sets would turn a clean *semiconductor* signal
into a noisy *ICT hardware* one.

## Caveats

- **HS revision.** Codes are HS2017 (OECD) / recent (Fed); the dashboard reads them against the
  HS2012 HS6 file. Most headings are revision-stable at HS6; `281212` has no HS2012 match (noted in
  `techai.json.missingCodes`).
- **No double-counting across tiers/baskets.** AI compute (8471/8473) is disjoint from the OECD set;
  Tier B headings (8517/8504/8534/…) are disjoint from both. A finished AI server (847150) and the
  chips inside it (854232) are *different HS lines* — complementary layers, not subsets.
- **Dual-use is irreducible at HS6.** You cannot isolate "data-center switches" from "telecom
  switches" within 851762 at this granularity; the only fix is finer national lines (HS8–10) or
  firm-level data.

## Recommendation

Implement **Tier B** as a new, separately-labeled basket group ("AI / data-center infrastructure")
in `classifications.py` → `techai.json`, alongside (not merged into) the Fed and OECD sets. Leave
**Tier C** out of the AI baskets (optionally expose as a clearly-marked "broad ICT/energy" overlay).
This keeps the silicon signal clean while adding the genuinely AI-driven infrastructure layer.

---

## Sourcing current *monthly* data (the Comtrade gap, national sources, Haver)

The dashboard runs on the reconciled **annual** Atlas (HS92 HS4). For a timely read, UN Comtrade
has **monthly** HS6 — but for these codes only ~32 of the 50 tracked economies report a current
(2026) month, and crucially **the biggest chip/AI hubs are missing or lagged: Taiwan, China,
Singapore, Vietnam** (Comtrade frontier ≈ Mar-2026; China/Taiwan absent). National customs sources
fill the gap, with very different accessibility (probed 2026-06):

| hub (source) | anti-bot? | HS6 detail public & free? | verdict |
|---|---|---|---|
| **Taiwan — MOF/DGoC** ([portal.sw.nat.gov.tw](https://portal.sw.nat.gov.tw/APGA/GA30E)) | none | **yes** — HS 2/4/6/8/11, USD, English, fast (~10-day lag) | **easiest; dashboard-grade** |
| **China — GACC** ([stats.customs.gov.cn](http://stats.customs.gov.cn/)) | **yes (瑞数 WAF; HTTP 412 on every endpoint)** | exists at HS8 but **walled** | manual-in-browser only; automation hard/fragile/ToS-gray. English site = aggregates only |
| **Vietnam — GDVC/GSO** ([customs.gov.vn](https://www.customs.gov.vn/)) | none (HTTP 200) | **no** — only a broad "electronics" group free; HS8 in VN-language reports | easy to reach, but **coarse**; HS6 is a manual dig |

Difficulty is set by the **gateway, not the code count** — scraping a few HS6 from GACC is no easier
than many (the 瑞数 challenge gates all requests). For a handful of codes, GACC is trivial *manually*
(real browser → query China's HS8, first 6 = our HS6 → export Excel) but not worth automating;
Taiwan is the clean programmatic win; Vietnam is open but its free data stops at "electronics."

### Haver series tracked (in the `haver-data` pipeline, not this repo)

Haver's `emergepr` database carries these hubs' trade as **curated national aggregates** — timely
(**Apr-2026** for TW/CN/SG, **May-2026** for KR via flash releases — *ahead of Comtrade*). Added
2026-06-05 to `haver-data` (`config/series.yaml`); refreshed daily. **`code@emergepr`:**

| code | series (units) |
|---|---|
| `n528ievs` / `n528invs` / `n528invr` | Taiwan Exports ICs / Imports ICs / Imports Semiconductor Equipment (Mil US$) |
| `n924ie7f` / `n924in5l` / `n924in3p` | China Exports IC / Imports IC / Imports Semiconductor Mfg Equip (Mil USD) |
| `n542ixvr` / `n542imvr` | South Korea Exports / Imports Semiconductors (Thous US$) |
| `n576invs` | Singapore NODX: Integrated Circuits (**Mil S$** — local currency) |
| `n582ixe` / `n582ime` | Vietnam Exports / Imports: Computers, Electronic Products & Parts (Mil US$) |

**Why these are *not* dashboard-grade** (monitoring only): mixed units (USD / Thous US$ / local S$),
mixed concepts ("Integrated Circuits" vs broad "Semiconductors" vs "Computers/electronics"), and
curated aggregates rather than the HS6 basket structure. Taiwan is the exception — `emergepr` even
splits IC / DRAM / semiconductor-equipment / chemical-wafer **bilaterally by partner** (finer than HS6).

### Do the Haver aggregates map to HS6? — Vietnam check

To test whether a Haver national aggregate is a recognizable HS6 sum, we compared Vietnam's Haver
"Computers, Electronic Products & Parts" (2024 annual) against Harvard HS6 sums for Vietnam 2024:

| basket (Harvard HS6, VNM 2024) | export $B | vs Haver $72.6B | import $B | vs Haver $107.1B |
|---|---|---|---|---|
| `8471`+`8473`+`8541`+`8542` (computers, parts, semis, ICs) | 82.7 | **114%** | 70.3 | 66% |
| + broad electronics, **excl. phones** | 116.9 | 161% | 87.4 | 82% |
| + `8517` (incl. phones/telecom) | 178.8 | 246% | 105.0 | 98% |

**Finding:** yes — it is a recognizable HS6 electronics aggregate that **excludes mobile phones**
(`8517`, $61.9B, which Vietnam reports as a separate "phones & parts" category; including it
overshoots exports to 246%). On exports it tracks the **computers + ICs + semiconductors + parts**
set (`8471/8473/8541/8542`), Haver ≈ 88% of that basket. The match is only approximate (~15–35%)
because Haver is **Vietnam's own customs** while Harvard is **Atlas mirror-reconstructed** (its VNM
total runs high at ~$429B vs Vietnam's reported ~$405B), and the category's exact HS boundaries
differ. Takeaway: Haver aggregates are *interpretable* as HS-code groups for sanity/monitoring, but
the source and boundary differences are why they aren't a clean substitute for the HS6 baskets.
