# EDGAR Historical Data: Terminology Guide

This guide explains the fields and terms in the SEC EDGAR **Company Facts** bulk dataset (`companyfacts.zip`), which [`HistoricalEdgarFetcher`](../../core/ingestion_worker/sources/historical_edgar.py) downloads and parses.

- **Source:** `https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip`
- **Local copy:** `core/ingestion_worker/.data/sec_historical/companyfacts/` (about 20,000 files, one per company)
- **Official docs:** [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)

---

## Background concepts

| Term | Meaning |
|------|---------|
| **SEC** | U.S. Securities and Exchange Commission. Public companies must file financial reports with it. |
| **EDGAR** | *Electronic Data Gathering, Analysis, and Retrieval*: the SEC's system for filings. |
| **XBRL** | *eXtensible Business Reporting Language*: a machine-readable format. Companies tag every number in their filings with a standard concept name (for example `Revenues`), so the values can be extracted automatically. This dataset is built from those tags. |
| **Company Facts** | Every XBRL-tagged value a company has ever reported, collected into one JSON file. |
| **CIK** | *Central Index Key*: the SEC's permanent numeric ID for a filer. File names use the 10-digit zero-padded form (`CIK0000320193.json` is Apple). Tickers can change, CIKs don't. Ticker-to-CIK mapping: <https://www.sec.gov/files/company_tickers.json>. |
| **Fact** | A single reported value: one number, for one concept, for one period, from one filing. |

---

## File structure

```text
CIK0000320193.json
├── cik            320193
├── entityName     "Apple Inc."
└── facts
    └── <taxonomy>                 e.g. "us-gaap"
        └── <concept>              e.g. "EarningsPerShareBasic"
            ├── label              human-readable name
            ├── description        accounting definition
            └── units
                └── <unit>         e.g. "USD/shares"
                    └── [ fact, fact, ... ]   the timeline of reported values
```

### Top-level fields

| Field | Example | Meaning |
|-------|---------|---------|
| `cik` | `320193` | The company's CIK, as an integer (not padded). |
| `entityName` | `"Apple Inc."` | The company's registered legal name. |
| `facts` | `{...}` | All facts, grouped by taxonomy. |

---

## Taxonomies

A **taxonomy** is a standard dictionary of concept names. Each key under `facts` is a taxonomy prefix.

| Prefix | Name | What's in it |
|--------|------|--------------|
| `us-gaap` | U.S. Generally Accepted Accounting Principles | Core financial statement items: revenue, net income, assets, liabilities, cash flow, EPS. **This is the main one.** |
| `dei` | Document and Entity Information | Cover page data: shares outstanding (`EntityCommonStockSharesOutstanding`), public float (`EntityPublicFloat`). |
| `ifrs-full` | International Financial Reporting Standards | Used by foreign filers in place of `us-gaap`, usually with a `20-F` or `40-F`. |
| `srt` | SEC Reporting Taxonomy | Supplementary items shared across industries. |
| `ffd` | Filing Fee Disclosures | Registration fee data from offering filings (`NetFeeAmt`). Usually not useful for financial analysis. |
| `ecd` | Executive Compensation Disclosure | Pay-versus-performance data from proxy statements. |
| `invest` | Investment Company | Data reported by investment companies. |
| `cef`, `vip`, `rxp` | Closed-end funds, variable insurance products, resource extraction payments | Specialised, rarely seen. |

---

## Concepts

A **concept** (also called an *element* or *tag*) is one kind of financial item, such as `AccountsPayable` or `RevenueFromContractWithCustomerExcludingAssessedTax`.

| Field | Meaning |
|-------|---------|
| *key* | The machine name of the concept (CamelCase). |
| `label` | The human-readable name. It can include notes such as `(Deprecated 2009-01-31)`, which means the taxonomy has since replaced that concept. Sometimes it is an empty string. |
| `description` | The formal accounting definition. These are often long. Sometimes empty, sometimes `null`. |
| `units` | Facts grouped by unit of measure. |

> **Note:** Companies don't always use the same concept for the same item. Revenue, for example, can appear as `Revenues`, `SalesRevenueNet` (older filings), or `RevenueFromContractWithCustomerExcludingAssessedTax` (ASC 606, 2018 onward). To get a full history you may need to combine several concepts.

---

## Units

The keys under `units` give the unit of measure.

| Unit | Meaning |
|------|---------|
| `USD` | U.S. dollars. Values are in whole dollars, not thousands or millions: `383285000000` is $383.3 billion. |
| `shares` | Number of shares. |
| `USD/shares` | Dollars per share, as in EPS and dividends per share. |
| `pure` | A dimensionless number such as a ratio or percentage. Percentages are stored as decimals (`0.21` = 21%). |
| `JPY`, `EUR`, `CAD`, `GBP`, ... | Other currencies (ISO 4217 codes), mostly from foreign filers. |
| `CAD/shares` etc. | Per-share amounts in another currency. |
| `segment`, `loan`, `item`, `contract`, ... | Counts of things. |

---

## Fact fields

Every entry in a unit's array is one fact. Example (Apple, basic EPS):

```json
{
  "start": "2022-09-25",
  "end":   "2023-09-30",
  "val":   6.16,
  "accn":  "0000320193-25-000079",
  "fy":    2025,
  "fp":    "FY",
  "form":  "10-K",
  "filed": "2025-10-31",
  "frame": "CY2023"
}
```

| Field | Always present? | Meaning |
|-------|-----------------|---------|
| `val` | yes | The reported value. |
| `end` | yes | The date the value applies to: either the end of the period, or the point in time for a balance. |
| `start` | only for **duration** facts | Start of the period the value covers. See [Instant vs. duration](#instant-vs-duration-facts). |
| `accn` | yes | *Accession number*: the unique ID of the filing the fact came from. Format: `<filer-or-agent CIK>-<YY>-<sequence>`. |
| `fy` | yes (may be `null`) | Fiscal year **of the filing**, not of the value. See [the warning below](#fy-fp-and-form-describe-the-filing-not-the-value). |
| `fp` | yes (may be `null`/`""`) | Fiscal period **of the filing**: `FY` (full year, annual report), `Q1`, `Q2`, `Q3`. `Q4` and `CY` are rare. There is usually no Q4 filing because the 10-K covers the fourth quarter. |
| `form` | yes | Type of SEC form the fact was reported in. See [Form types](#form-types). |
| `filed` | yes | Date the filing was submitted to the SEC. |
| `frame` | sometimes | The SEC's calendar-aligned label for the value. See [Frames](#frames). |

### Instant vs. duration facts

- **Instant** facts have no `start`. They are a snapshot on the `end` date: balance-sheet items (assets, cash, debt) and shares outstanding. *"Cash was $X as of 2023-09-30."*
- **Duration** facts have a `start` and an `end`. They measure activity over a period: income-statement and cash-flow items (revenue, net income, EPS). *"Revenue was $X from 2022-09-25 to 2023-09-30."*

The length of the period (`end` − `start`) tells you whether a duration value is quarterly (~90 days), year-to-date (~180 or ~270 days), or annual (~365 days). A `10-Q` for Q3 often reports both the 3-month and the 9-month figure.

### `fy`, `fp`, and `form` describe the filing, not the value

This is the most common source of confusion. A filing restates figures from earlier periods for comparison, and each restatement is listed as a separate fact. Apple's FY2023 revenue appears three times:

| `start` → `end` | `val` | `form` | `fy` | `fp` | `filed` | `frame` |
|---|---|---|---|---|---|---|
| 2022-09-25 → 2023-09-30 | 383,285,000,000 | 10-K | 2023 | FY | 2023-11-03 | |
| 2022-09-25 → 2023-09-30 | 383,285,000,000 | 10-K | 2024 | FY | 2024-11-01 | |
| 2022-09-25 → 2023-09-30 | 383,285,000,000 | 10-K | 2025 | FY | 2025-10-31 | `CY2023` |

So `fy: 2025` means *"taken from the FY2025 annual report,"* not *"this is 2025 revenue."* To find which period a value covers, use `start`/`end` or `frame`.

### Frames

A `frame` is the SEC's single, deduplicated value for a concept in a **calendar** period. The SEC assigns one fact per company per concept per frame, picked from among the duplicates, so filtering to facts that have a `frame` is a simple way to remove duplicates.

| Pattern | Example | Meaning |
|---------|---------|---------|
| `CY####` | `CY2023` | Annual duration (about 365 days) aligned to calendar year 2023. |
| `CY####Q#` | `CY2023Q2` | Quarterly duration (about 91 days) aligned to that calendar quarter. |
| `CY####Q#I` | `CY2023Q2I` | **I**nstant value at the end of that calendar quarter. |

Frames are calendar-based even when the company's fiscal year isn't. Apple's fiscal year ends in late September, but its FY2023 is framed as `CY2023` because that is the closest calendar year. Year-to-date durations such as 6- or 9-month figures never get a frame.

---

## Form types

The forms you'll see most often (counts from a sample of the local dataset):

| Form | Meaning |
|------|---------|
| `10-K` | Annual report from a U.S. company. Audited. `fp` is usually `FY`. |
| `10-Q` | Quarterly report from a U.S. company, filed for Q1–Q3. Unaudited. |
| `20-F` | Annual report from a foreign private issuer. |
| `40-F` | Annual report from certain Canadian issuers. |
| `6-K` | Interim or current report from a foreign issuer. |
| `8-K` | Current report on a material event (often an earnings release). |
| `10-KT` / `10-QT` | *Transition* report, filed when a company changes its fiscal year end. Covers an unusual period length. |
| `DEF 14A` / `PRE 14A` | Proxy statement (definitive or preliminary) for shareholder meetings. Source of `ecd` executive pay data. |
| `S-1`, `S-3ASR`, `S-8`, `424B2`, `424B5` | Securities registration or prospectus filings. Mostly the source of `ffd` fee data. |
| `N-4` etc. | Investment company / insurance product filings. |

**Suffixes:**

- `/A` (e.g. `10-K/A`) is an **amendment** that corrects or adds to an earlier filing. Its values replace the original's.
- `R` in `DEFR14A` means *revised*.

---

## Common financial abbreviations

| Term | Meaning |
|------|---------|
| **GAAP** | Generally Accepted Accounting Principles: the U.S. accounting rulebook. |
| **IFRS** | International Financial Reporting Standards: the rulebook used in most other countries. |
| **EPS** | Earnings per share: net income ÷ shares. *Basic* uses actual shares. *Diluted* also counts options, convertibles, and similar securities that could become shares. |
| **Public float** | Market value of shares held by the public (not insiders). |
| **Fiscal year (FY)** | The company's own 12-month reporting year. It may not match the calendar year. |
| **ASC 606** | The revenue recognition standard adopted in 2018, which brought in `RevenueFromContractWithCustomer...` concepts. |
| **Deprecated** | A concept the taxonomy has since replaced. Older filings still use it. |

---

## How this project uses the data

[`_convert_edgar_json_to_text`](../../core/ingestion_worker/sources/historical_edgar.py) turns each fact into its own `FinancialDocument`. The document's `content` is one sentence:

```text
In the {form} filing for fiscal year {fy} period {fp}, {entityName} reported
{label} of {val} {unit} as of {end}.
```

The concept's `description` goes in the document's separate `description` field, not in the sentence. The `filed` date becomes the document's `publish_date`.

Given the terminology above, keep these limitations in mind:

1. **`fy`/`fp` are filing labels.** The sentence "fiscal year 2025 … as of 2023-09-30" is accurate but can mislead a retriever or LLM. Using `frame`, or `start`/`end`, would describe the period more clearly.
2. **`start` is ignored.** Duration facts read like instant facts, so a 3-month value and a 9-month value with the same `end` become hard to tell apart.
3. **Duplicates are kept.** Every restatement becomes its own sentence. Filtering to facts with a `frame` (or deduplicating on concept + unit + start + end) would shrink the corpus a lot.
4. **All taxonomies are included.** `ffd` and `ecd` facts are rarely useful for financial Q&A.
5. **Descriptions are repeated in every document.** The sentence no longer includes the definition, but each fact's document still stores its concept's full `description`, so the same long text is kept once per fact.
