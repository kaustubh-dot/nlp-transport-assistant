# Language and Robustness Specification (Phase N4)

Document: `docs/nlp_v2/language_and_robustness_spec.md`  
Snapshot Version: `chennai_multimodal_v1.2.1`  
Date: 2026-09-19  
Status: Authoritative Language & Robustness Framework (Corrected Methodology Patch)

---

## 1. Multilingual Scope and Taxonomy

The primary v2 NLP benchmark covers four linguistic strata across two scripts (Latin and Devanagari), reflecting the genuine linguistic reality of Chennai commuters.

### 1.1 Five Formal Language Classes

| Language Code | Script | Description | Pilot/Default Proposal (%) | Representative Query Example |
| :--- | :--- | :--- | :---: | :--- |
| **`EN`** | Latin (`Latn`) | Monolingual English transit query | 25% (Proposal) | "What is the earliest metro from Central to Airport?" |
| **`HI_DEVA`** | Devanagari (`Deva`) | Monolingual Hindi in Devanagari script | 25% (Proposal) | "चेन्नई सेन्ट्रल से एयरपोर्ट के लिए पहली मेट्रो कितने बजे है?" |
| **`HI_LATN`** | Latin (`Latn`) | Monolingual Hindi in Roman script (pure Roman Hindi) | 15% (Proposal) | "chennai central se airport ke liye pehli metro kitne baje hai?" |
| **`HINGLISH_LATN`** | Latin (`Latn`) | Code-mixed Hindi and English in Latin script | 25% (Proposal) | "central se airport ka first metro timing kya hai schedule batao" |
| **`MIXED_SCRIPT_CS`** | Mixed (`Deva` + `Latn`) | Intra-sentential code-switching across scripts | 10% (Proposal) | "Central से Airport के लिए first metro कब departure karti hai?" |

*Status Note on Proportions*: The 25/25/15/25/10 distribution is a starting proposal for pilot synthesis. Final proportions will be determined experimentally in the Language-Mixture study (preregistered across all 5 classes).

*Tamil Scope Note*: Tamil station and stop names in `canonical_transport.db` (421 verified Tamil strings) participate in entity resolution and alias evaluation. Monolingual Tamil intent classification is deferred to a future phase to preserve research depth on Hindi-English code-switching.

### 1.2 Language Metadata Schema

Every utterance in the v2 dataset carries structured linguistic metadata:

```json
{
  "language_code": "HINGLISH_LATN",
  "primary_language": "hi",
  "secondary_language": "en",
  "script": "latin",
  "code_switched": true,
  "romanized": true,
  "code_switch_level": "CS2",
  "noise_level": "N2"
}
```

---

## 2. Code-Switch Intensity Taxonomy (CS0 to CS4)

Code-switching is not a binary flag. It ranges from isolated loanwords to dense syntactic alternating frames.

| Level | Formal Definition | Grammatical Structure | Concrete Commuter Examples |
| :---: | :--- | :--- | :--- |
| **`CS0`** | **Pure Monolingual** | Zero code-mixing. Pure English or pure Devanagari Hindi. | EN: "How do I get from Guindy to Central?"<br>HI: "गिंडी से सेन्ट्रल जाने का रास्ता बताओ।" |
| **`CS1`** | **Borrowed Transit Lexicon** | Single-language syntax with isolated borrowed transit nouns (`metro`, `bus`, `ticket`, `station`, `platform`). | EN: "Is there any local train from Tambaram to Beach?"<br>HI: "गिंडी से एयरपोर्ट के लिए कौन सी metro मिलेगी?" |
| **`CS2`** | **Light Code-Switching** | Dominant Hindi matrix language with English noun/verb phrases. | Hinglish: "Guindy se Airport ka best route kya hai?"<br>Hinglish: "Central station me parking facility available hai kya?" |
| **`CS3`** | **Dense Code-Switching** | Balanced mixing of Hindi and English clauses, alternating function words. | Hinglish: "Guindy to Central metro route me kitna travel time lagta hai?"<br>Deva+Latn: "Guindy se Airport jaane ke liye metro available hai kya?" |
| **`CS4`** | **Heavy / Mixed-Script Switching** | Rapid intra-sentential switching across both languages and scripts. | Mixed: "Guindy से Airport ke liye kaun si metro best rahegi please tell?"<br>Mixed: "Central station par bus to metro interchange possible hai?" |

---

## 3. Spelling & Robustness Noise Taxonomy (N0 to N5)

Real commuter typing exhibits heavy orthographic variation, phonetic spelling, and chat abbreviations.

**Crucial Research Principle**:
Surface noise must NOT be normalized during dataset creation. Raw, noisy surface strings must be preserved in the benchmark. Normalization is an experimental pipeline component whose effectiveness must be empirically proven.

| Noise Tier | Noise Name | Operational Rules & Transformations | Examples |
| :---: | :--- | :--- | :--- |
| **`N0`** | **Canonical Ground Truth** | Official canonical spelling, standard casing, clean punctuation. | `Guindy`, `Chennai Central`, `102A`, `first metro` |
| **`N1`** | **Case & Punctuation Drift** | Missing capitalization, extra spaces, missing question marks, erratic hyphens. | `guindy`, `chennai central`, `102 a`, `first metro?` |
| **`N2`** | **Common Transliteration Drift** | Common phonetic Romanization variants of Indic names and Hindi words. | `gindi`, `guindi`, `kese` (kaise), `jaana` (jana), `h` (hai), `kaha` (kahan) |
| **`N3`** | **Typographical Keyboard Noise** | QWERTY adjacent key swaps, single character insertions or deletions ($\le 1$ edit distance). | `gundy`, `cntral`, `metor`, `timig`, `tikcet` |
| **`N4`** | **Chat Abbreviations & Slang** | Commuter SMS/chat contractions and transit abbreviations. | `stn` (station), `bs` (bus stand), `bt` (bus terminus), `jn` (junction), `rd` (road), `kb` (kab), `bje` (baje) |
| **`N5`** | **Severe Interpretable Corruption** | Combination of transliteration variation, typo, and abbreviation. Must remain human-readable. | `gindy stn se ayrport kse jye`, `cntrl to tbm local trn k bje h` |

*Exclusion Rule*: Nonsensical adversarial string scrambles (e.g. `xqzj89Tambaram`) are strictly forbidden. All noise tiers must reflect documented SMS and chat habits of Indian urban commuters.

---

## 4. Transliteration vs Translation Distinction

The research program enforces rigid conceptual boundaries between transliteration, entity resolution, and translation:

```
TRANSIT DIALOGUE DISTINCTIONS:

1. Transliteration (Script Mapping):
   "गिंडी" (Devanagari)  →  "gindi" (Latin script)
   Character-by-character phonetic transcription; does not alter meaning or language.

2. Entity Resolution (Canonical Grounding):
   "gindi" / "गिंडी" / "கிண்டி"  →  HUB_GUINDY (Canonical Database ID)
   Grounds arbitrary surface strings into the authoritative transit knowledge base.

3. Machine Translation (Cross-Lingual Transfer):
   "मुझे गिंडी जाना है" (Hindi)  →  "I want to go to Guindy" (English)
   Translates syntactic structure and vocabulary across language boundaries.
```

Collapsing these tasks causes acute system failures, such as translation engines translating "High Court" into Hindi "उच्च न्यायालय" (Ucch Nyayalay) or "Light House" into "प्रकाश स्तंभ" (Prakash Stambh), breaking station entity matching against local transit signage.

---

## 5. Controlled Lexical Variation & Ambiguity Handling

To ensure natural linguistic diversity in synthesized families, the generator draws from realistic variation pools while respecting ambiguity rules:

### Hindi / Hinglish Transit Function Words:
- `kaise` (how): `kaise`, `kese`, `kaiseh`, `kis tarah`, `kaise jau`, `kaha se`
- `jana` (go): `jana`, `jaana`, `janaa`, `pahuchna`, `pahuche`, `travel kare`
- `hai` (is): `hai`, `h`, `hain`, `he`
- `kab` (when): `kab`, `kis samay`, `kitne baje`, `kb`
- `chahiye` (want/need): `chahiye`, `chaiye`, `chahie`
- `milegi` (will get): `milegi`, `mil sakti hai`, `available hai kya`

### Transit Facility Abbreviations:
- `station` → `station`, `stn`, `sttn`
- `bus stand` → `bus stand`, `bs`, `b.s.`, `bus stop`
- `bus terminus` → `bus terminus`, `bt`, `b.t.`, `terminus`
- `junction` → `junction`, `jn`, `junc`
- `road` → `road`, `rd`, `salai`

### Strict Zero-Default Rule for Ambiguous Time and Relative Days:
1. Bare times (`8 baje`, `8 बजे`) must **not** default to 08:00. Dual candidates `08:00:00` and `20:00:00` are retained with `temporal_ambiguity = true`.
2. Relative day `कल / kal` must **not** default to tomorrow. It is resolved to `+1` (tomorrow) or `-1` (yesterday) solely when auxiliary verbs or tense markers provide unambiguous grammatical evidence; otherwise, an explicit unresolved ambiguity flag is emitted.
