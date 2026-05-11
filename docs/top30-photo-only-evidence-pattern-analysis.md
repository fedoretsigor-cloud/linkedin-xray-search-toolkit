# Top 30 Photo-only Evidence Pattern Analysis

Date: 2026-05-11

Baseline saved list: `docs/We found Front Office Power Business Analyst.md`
Baseline run: `dfad1f70dd`
Search: `Front Office Power Business Analyst`
Location: `Houston, United States`

This analysis covers 30 strong candidates that appear in the photo set but were not in the saved `We found Front Office Power Business Analyst` list.

Important note: this is not a full profile scrape. The classification is based on the visible photo evidence, the saved-run query audit, and public web spot checks where available. The saved run used 10 unique query strings, and every one required the exact phrase `"Business Analyst"` plus `"Front Office"`. That explains why many strong profiles were missed.

## Definitions

### Evidence Core

High-precision evidence. Use when the profile has direct role/function evidence plus domain/tool evidence plus location.

Typical shape:

```text
("Business Analyst" OR BA OR "Business Systems Analyst" OR "Technical Business Analyst" OR "Business/Technical Analysis")
+
(ETRM OR CTRM OR Endur OR OpenLink OR RightAngle OR Allegro OR "Energy Trading" OR "Power Trading" OR "Gas Trading")
+
("Houston" OR "Greater Houston")
```

### Evidence Expansion

Recall-oriented evidence. Use when the person is likely relevant but the public role is not BA-shaped. These queries catch consultants, SMEs, leads, architects, developers, support engineers, and trading/risk systems people.

Typical shape:

```text
(Consultant OR SME OR Specialist OR Lead OR Architect OR Developer OR "Support Engineer" OR "Systems Lead")
+
(ETRM OR CTRM OR Endur OR OpenLink OR RightAngle OR Allegro OR "Trade Capture" OR "Trading Systems")
+
("Houston" OR "Greater Houston")
```

## Top 30 Classification

| # | Candidate | Visible evidence from photo/public check | Best lane | Query pattern that should find them | Why old query missed |
|---:|---|---|---|---|---|
| 1 | Dhyan Pai | OpenLink Endur Consultant; E/CTRM; Houston | Evidence Expansion | `(OpenLink OR Openlink OR Endur) (Consultant OR "Functional Consultant") (ETRM OR CTRM) Houston` | Consultant, not BA; old query lacked OpenLink |
| 2 | Gourav Roy | Global Energy Trading Systems Lead; Front-Office Trading Desk; Trade Capture; Endur; LNG/Gas | Evidence Expansion | `("Front-Office Trading Desk" OR "Trade Capture" OR "Trading Systems Lead") Endur ("Energy Trading" OR LNG OR Gas)` | Systems Lead, not BA; may have weak public indexing/location |
| 3 | Piyush Srivastava | Business Analyst - Endur; Greater Houston | Evidence Core | `("Business Analyst" OR BA) Endur ("Houston" OR "Greater Houston")` | No exact Front Office anchor |
| 4 | Viraj P | Sr. IT Business Analyst; ETRM/CTRM; Endur Specialist; OpenLink; Houston | Evidence Core | `("IT Business Analyst" OR "Business Analyst") (ETRM OR CTRM) (Endur OR OpenLink OR Openlink) Houston` | Old query lacked ETRM/CTRM/OpenLink lane and required Front Office |
| 5 | Angela Toliver | Business Analyst; Compliance; ETRM & CRM Implementation; Houston | Evidence Core | `"Business Analyst" (ETRM OR "ETRM Implementation") (Compliance OR CRM) Houston` | No Front Office exact phrase |
| 6 | Krishna M. | Senior Business Analyst; Nat Gas/LNG commodities; Endur V19; Houston | Evidence Core | `("Senior Business Analyst" OR "Business Analyst") (Endur OR ETRM) ("Natural Gas" OR LNG OR commodities) Houston` | No Front Office exact phrase |
| 7 | Mosin A. | OpenLink Endur Specialist; energy trading; Houston | Evidence Expansion | `(OpenLink OR Openlink OR Endur) (Specialist OR SME OR Consultant) "energy trading" Houston` | Specialist, not BA; old query lacked OpenLink |
| 8 | Alan Levine | ETRM Consultant; Energy Trading; Risk & Operations; Houston | Evidence Expansion | `"ETRM Consultant" "Energy Trading" (Risk OR Operations) Houston` | Consultant, not BA; no exact Front Office |
| 9 | Omar T. | Senior Front Office Commodities CTRM Developer; Front Office Developer; Greater Houston | Evidence Expansion | `("Front Office" OR "Front-Office") CTRM (Developer OR Architect) ("Houston" OR "Greater Houston")` | Developer, not BA; old query did not include CTRM/developer |
| 10 | Vishvesh Raiter | IT Program Manager/Business Analyst; Energy Trading and Risk Management; ETRM; Houston | Evidence Core | `("Business Analyst" OR "Program Manager") ("Energy Trading and Risk Management" OR ETRM) Houston` | Role text is broader than exact BA + Front Office |
| 11 | Ashish Gupta | Principal Consultant/Architect/Developer/BA for ETRM/CTRM/Endur/RightAngle; Houston | Evidence Core | `(BA OR "Business Analyst") (ETRM OR CTRM OR Endur OR RightAngle) Houston` | BA appears inside a mixed headline; old query lacked CTRM/RightAngle |
| 12 | Jacob Duncan | Business Analyst - Gas and Power Trading; Houston | Evidence Core | `"Business Analyst" ("Gas and Power Trading" OR "Power Trading" OR "Gas Trading") Houston` | No exact Front Office/tool anchor |
| 13 | Brent Breaux | Trading Systems BA; Products & Gas Trading; Front and Back Office; Greater Houston | Evidence Core | `("Trading Systems BA" OR BA) ("Front and Back Office" OR "Products & Gas Trading") ("Houston" OR "Greater Houston")` | Phrase is not exact `Front Office`; old query lacked trading-systems BA |
| 14 | Gerry Medeles | Senior Business Analyst at Shell Trading; Greater Houston | Evidence Core | `"Senior Business Analyst" "Shell Trading" ("Houston" OR "Greater Houston")` | No Front Office/tool term in visible text |
| 15 | Abdullah S | Digital Technology Leader; ETRM SME; Houston | Evidence Expansion | `(ETRM OR CTRM) (SME OR "Technology Leader") Houston` | SME/leader, not BA |
| 16 | Marcus Brown | Managing Delivery Consultant; ETRM OpenLink System Delivery; Greater Houston | Evidence Expansion | `(ETRM OR OpenLink OR Openlink) ("Delivery Consultant" OR Consultant OR "System Delivery") ("Houston" OR "Greater Houston")` | Delivery consultant, not BA; old query lacked OpenLink |
| 17 | Sowmy Vijayaraghavan | ETRM; Business Architecture; Solution Architecture; Business/Technical Analysis; Houston | Evidence Core | `(ETRM OR CTRM) ("Business Architecture" OR "Business/Technical Analysis" OR "Business Analysis") Houston` | No exact Business Analyst title/front-office anchor |
| 18 | Sid Kotha | Market/Credit Risk applications; SME; Senior Business Analyst at Shell Trading; Greater Houston | Evidence Core | `("Senior Business Analyst" OR SME) ("Shell Trading" OR "Market Risk" OR "Credit Risk") ("Houston" OR "Greater Houston")` | Domain is risk apps/Shell Trading, not Front Office exact |
| 19 | Jessie Jewell | Business Analyst at Shell; ETRM/Compliance; ETRM Endur; Houston | Evidence Core | `"Business Analyst" Shell (ETRM OR Endur OR Compliance) Houston` | No Front Office exact phrase |
| 20 | Israr Mandalvadi | Principal Consultant at Capco; ETRM/Endur; Houston | Evidence Expansion | `(Capco OR Consultant) (ETRM OR Endur) Houston` | Consultant, not BA |
| 21 | Moniz Mohammed | Trading & Risk Management Consultant at Capco; ETRM/Endur; Houston | Evidence Expansion | `("Trading & Risk Management" OR "Trading and Risk Management") Consultant (ETRM OR Endur OR Capco) Houston` | Consultant, not BA; old query lacked trading-risk phrase |
| 22 | Santhosh DS | Senior Manager; Sapient Global Markets; Senior Manager ETRM; ETRM/Endur; Houston | Evidence Expansion | `("Senior Manager" OR Manager) (ETRM OR Endur) ("Sapient Global Markets" OR Houston)` | Manager, not BA |
| 23 | Bhakta Ram | Energy commodities/capital markets trading and risk mgmt; ETRM/CTRM; OpenLink Endur; Houston | Evidence Expansion | `("Trading and Risk" OR "Trading and Risk Management") (ETRM OR CTRM OR OpenLink OR Endur) Houston` | Strong tools/domain, but no BA/Front Office exact |
| 24 | Rick Lundquist | Energy Trading Systems and Integration Delivery; ETRM Implementation Business Analyst; Allegro; Houston | Evidence Core | `("ETRM Implementation Business Analyst" OR "Business Analyst") (Allegro OR ETRM OR "Energy Trading Systems") Houston` | Old query lacked Allegro/trading systems |
| 25 | Stephen Mink | Energy Markets Technologist; ETRM Architect; Risk Analytics; Greater Houston | Evidence Expansion | `("ETRM Architect" OR "Energy Markets Technologist") ("Risk Analytics" OR ETRM) ("Houston" OR "Greater Houston")` | Architect/technologist, not BA |
| 26 | Laurel Adams Lloyd | ETRM Software Consultant; ETRM/Endur; Greater Houston | Evidence Expansion | `"ETRM Software Consultant" (Endur OR ETRM) ("Houston" OR "Greater Houston")` | Consultant, not BA |
| 27 | Howard Camp | ETRM Business Analyst; Senior Accountant; Houston | Evidence Core | `"ETRM Business Analyst" Houston` | No exact Front Office |
| 28 | Karl Schroeder | Sr Endur Business Analyst at Shell; Houston in photo | Evidence Core | `("Sr Endur Business Analyst" OR "Endur Business Analyst") Shell Houston` | No Front Office exact phrase |
| 29 | Richard Poterek | ION RightAngle Functional/Technical Lead; Openlink/Solarc RightAngle Developer; Houston | Evidence Expansion | `(RightAngle OR "ION RightAngle" OR Solarc OR Openlink) ("Functional Lead" OR "Technical Lead" OR Developer) Houston` | Lead/developer, not BA; old query lacked RightAngle/Solarc |
| 30 | Hubert Phillips | Endur BA/Tech; OpenLink Financial; Greater Houston | Evidence Core | `("Endur BA" OR "Endur BA/Tech" OR "Business Analyst") ("OpenLink Financial" OR OpenLink OR Endur) ("Houston" OR "Greater Houston")` | BA abbreviation and OpenLink wording were not covered |

## What This Means Architecturally

### Evidence Core should replace title-first as the main search shape

The strongest misses were not random. Many would be caught by a core query that does not force `Front Office`:

```text
site:linkedin.com/in/ ("Business Analyst" OR BA OR "Business Systems Analyst" OR "Technical Business Analyst")
(ETRM OR CTRM OR Endur OR OpenLink OR Openlink OR RightAngle OR Allegro)
("Houston" OR "Greater Houston")
```

Another core lane should capture energy trading BA without requiring vendor tools:

```text
site:linkedin.com/in/ ("Business Analyst" OR BA)
("Energy Trading" OR "Power Trading" OR "Gas Trading" OR "Shell Trading" OR "Natural Gas" OR LNG)
("Houston" OR "Greater Houston")
```

### Evidence Expansion should be separate and controlled

Expansion finds many excellent people, but it also increases noise because it captures consultants, developers, architects, and managers.

It should be a distinct wave:

```text
site:linkedin.com/in/ (Consultant OR SME OR Specialist OR Lead OR Architect OR Developer OR "Support Engineer")
(ETRM OR CTRM OR Endur OR OpenLink OR Openlink OR RightAngle OR Allegro)
("Houston" OR "Greater Houston")
```

### Front Office should become a concept, not one exact phrase

Use these equivalents:

```text
"Front Office"
"Front-Office"
"Front-Office Trading Desk"
"Trade Capture"
"Front and Back Office"
"Trading Systems"
"Commercial Applications"
"Business Applications"
```

### Vendor vocabulary needs first-class treatment

The old run included `Endur` and `Orchestrade`, but missed important terms shown in the photo list:

```text
OpenLink
Openlink
ION OpenLink
RightAngle
Solarc
Allegro
Capco
KWA Analytics
Sapient Global Markets
```

## Recommended Wave Design

1. Evidence Core - BA/function + tool/domain + strict location.
2. Evidence Core - BA/function + energy trading domain + strict location.
3. Small title-precision lane - exact `Business Analyst + Front Office`, kept as a narrow precision signal, not the whole search.
4. Evidence Expansion - consultant/SME/lead/architect/developer + tool/domain + strict location.
5. Verification pass - for strong profiles with weak location snippets, verify by `name + profile + Houston`.

## Bottom Line

Of these 30 photo-only candidates:

- 15 are best found by Evidence Core.
- 15 are best found by Evidence Expansion.

So we should not use only one strategy. Evidence Core should become the default first wave. Evidence Expansion should be controlled by depth/budget, likely enabled for Max or when Core does not reach the target candidate count.
