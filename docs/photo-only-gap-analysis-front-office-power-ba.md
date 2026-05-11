# Photo-only Gap Analysis - Front Office Power Business Analyst

Date: 2026-05-11

Baseline saved list: `docs/We found Front Office Power Business Analyst.md`
Baseline run: `dfad1f70dd`
Search: `Front Office Power Business Analyst`
Location: `Houston, United States`

## Executive Summary

The saved run found 58 candidates. The photo set contains 85 unique people. Only 9 people overlap, leaving 76 photo-only people.

The most important finding: the saved run had breadth by provider/pages, but very little semantic breadth. It executed 310 provider/page requests, but only 10 unique query strings. Every unique query required `"Business Analyst"` and `"Front Office"`.

That means many strong ETRM/Endur/Houston profiles were missed because they use adjacent public titles:

- `Consultant`, `SME`, `Lead`, `Architect`, `Developer`, `Support Engineer`
- `Trading Systems`, `Trade Capture`, `Commercial Applications`, `Business Applications`
- `CTRM`, `OpenLink/Openlink`, `ION OpenLink`, `RightAngle`, `Allegro`
- `Front-Office`, `front-office technology`, `front and back office`
- `Middle Office`, `Settlements`, `Gas Scheduling`, `Market Risk`, `Credit Risk`

So the next improvement should not be simply more pages. It should be better semantic query families.

## Baseline Query Shape

All 10 unique queries were variations of this pattern:

```text
site:linkedin.com/in/ "Business Analyst" "Front Office" "Power Trading" "Endur" "houston"
```

The run did not include query terms like:

```text
Consultant
Lead
SME
Architect
Developer
OpenLink / Openlink
Trade Capture
Front-Office
Natural Gas
RightAngle
Allegro
Commercial Applications
Business Applications
```

## Full Photo-only Table

| # | Name | Evidence visible on photo | Likely reason missed | Pattern improvement |
|---:|---|---|---|---|
| 1 | Dhyan Pai | OpenLink Endur Consultant; Commodities Trading and Risk Management | Strong match, but title is `Consultant`, not `Business Analyst`; old query did not include `OpenLink` | Add ETRM consultant family: `("OpenLink" OR Openlink OR Endur) (Consultant OR SME) "Houston"` |
| 2 | Gourav Roy | Global Energy Trading Systems Lead; Front-Office Trading Desk Architecture; Trade Capture; Endur; Crude/Products/LNG Gas | Strong match, but title is `Systems Lead`; public search visibility may be weak; location proof may be only United States | Add trading systems lead family: `"Trade Capture" OR "Front-Office Trading Desk" OR "Trading Systems Lead"` |
| 3 | Vinay Nagulavancha | Energy Finance Professional; Natural Gas | Weak for this exact role; lacks BA/Front Office/ETRM/Endur evidence | Keep as low-priority adjacent energy finance pattern, not core Front Office BA |
| 4 | Amir Hasin Khan | Business Analyst; Capital Markets and Investment Banking; Houston | Has BA and Houston, but lacks energy/ETRM/front-office evidence | Add only if capital markets/front-office finance is in scope; otherwise low priority |
| 5 | Denise Weinberg | IT Risk CyberSecurity; AI; ETRM/CTRM; Project Manager | ETRM/CTRM match, but no BA/Front Office; title is PM/risk/cyber | Add ETRM/CTRM project/program manager alternate group |
| 6 | Mattice Evans | Project Manager; Scrum Master; Houston Oil & Gas | Too generic; no ETRM/Endur/front-office evidence | Keep filtered unless PM/Scrum in energy becomes explicit target |
| 7 | Piyush Srivastava | Business Analyst - Endur; Greater Houston | Strong match, but no `Front Office`; old query required `"Front Office"` | Add relaxed Endur BA group: `"Business Analyst" Endur "Houston"` |
| 8 | Viraj P | Sr. IT Business Analyst; ETRM/CTRM Endur Specialist; OpenLink; Houston | Strong match, but may miss exact Front Office anchor | Add `IT Business Analyst` + `ETRM/CTRM/OpenLink/Endur` group |
| 9 | Muzammil M Siddiqui | Regulatory Analyst; Houston Oil & Gas | Weak/adjacent; lacks BA/ETRM/Front Office | Keep low priority unless regulatory/settlements wave added |
| 10 | Angela Toliver | Business Analyst; Compliance; ETRM & CRM Implementation; Houston | Good match, but lacks Front Office and probably Endur | Add BA + ETRM implementation/compliance group |
| 11 | Hank Ceballos | Project Implementation Owner; ETRM; PCI Energy Solutions | ETRM project owner, not BA/Front Office | Add implementation owner/product owner ETRM group |
| 12 | Qi Yu | Senior Business Analyst; Houston | BA/Houston, but lacks energy/ETRM/front-office evidence | Needs energy/vendor qualifier; otherwise noisy |
| 13 | Krishna M. | Senior Business Analyst; Nat Gas and LNG commodities; Endur V19; Houston | Strong match, but no Front Office exact phrase | Add commodity BA group: `"Business Analyst" (LNG OR "Natural Gas") Endur Houston` |
| 14 | Mosin A. | Energy trading; OpenLink Endur Specialist; Houston | Strong tool/domain match, but title is Specialist | Add specialist/SME title alternates around OpenLink/Endur |
| 15 | Dhaval Dhere | Market Risk & Trading Analytics; Houston | Adjacent risk/trading analytics, no BA/ETRM | Add market risk/trading analytics only as later wave |
| 16 | Alan Levine | ETRM Consultant; Energy Trading; Risk & Operations; Houston | Strong match, but consultant not BA and no Front Office exact | Add `ETRM Consultant` + `Energy Trading` group |
| 17 | Omar T. | Senior Front Office Commodities CTRM Developer; Front Office Developer; Greater Houston | Strong match, but developer not BA; CTRM not in old query | Add Front Office CTRM developer/architect group |
| 18 | Daniel Faflik | Capital Markets IT; front-office technology; energy firms; Houston | Uses lowercase/hyphen-like `front-office technology`, not exact `Front Office`; not BA | Add front-office technology phrase variants |
| 19 | Vishvesh Raiter | IT Program Manager/Business Analyst; Energy Trading and Risk Management; ETRM; Houston | Good match, but role title too broad and likely no exact Front Office | Add program/product owner BA ETRM group |
| 20 | Prasad Challangi | ETRM Consultant; Houston | Strong adjacent, consultant not BA | Add ETRM consultant group |
| 21 | Runva C. | Renewable and traditional energy & commodities professional; Greater Houston | Energy/commodities but not BA/ETRM/front office | Low-priority broad energy commodities |
| 22 | Ashish Gupta | Principal Consultant/Architect/Developer/BA for ETRM/CTRM/Endur/RightAngle; Houston | Very strong, but many titles not exact BA; old query lacked CTRM/RightAngle | Add ETRM/CTRM/Endur/RightAngle consultant/architect/dev/BA group |
| 23 | Jacob Duncan | Business Analyst - Gas and Power Trading; Houston | Strong BA/domain match, but no Front Office exact | Add gas/power trading BA group |
| 24 | Brent Breaux | Trading Systems BA; Products & Gas Trading; Front and Back Office; Greater Houston | Strong, but phrase is `Front and Back Office`, not exact `Front Office` anchor | Add `Trading Systems BA` and `Front and Back Office` variants |
| 25 | Jason S. | Digital transformation across energy/utilities/oil and gas; Greater Houston | Too broad; no ETRM/BA/front-office visible | Keep filtered unless transformation leadership in scope |
| 26 | Gerry Medeles | Senior Business Analyst at Shell Trading; Greater Houston | Strong BA/trading match, but no Front Office/ETRM | Add Shell Trading/Senior BA energy trading group |
| 27 | Christopher Hartley | Global Trading; Houston | Too broad; no BA/ETRM/tool visible | Low priority |
| 28 | Abdullah S | Digital Technology Leader; ETRM SME; Houston | Strong ETRM SME, but not BA | Add ETRM SME/technology leader group |
| 29 | Justo Morales | Experienced Energy Consultant; Houston | Consultant/energy but no ETRM/Endur/front-office visible | Medium/low unless consulting wave includes vendor evidence |
| 30 | Marcus Brown | Managing Delivery Consultant; ETRM OpenLink System Delivery; Greater Houston | Strong ETRM/OpenLink delivery, but consultant/delivery not BA | Add ETRM OpenLink delivery consultant group |
| 31 | Subbu Chandrashekhar | Head of Business Applications; Houston | Business applications leader; weak visible ETRM evidence | Add only if commercial/business applications energy wave exists |
| 32 | Sheel Kakkar | KWA Analytics; Energy Trading & Risk Management; advisory/business consulting; Houston | Strong domain/vendor consulting, but no BA/Front Office exact | Add KWA/energy trading risk management consulting group |
| 33 | Ricky Price Jr. | Business Analyst; ISO Settlements; MCG Energy Solutions; Houston | Good adjacent BA, but settlements not in old terms | Add settlements/ISO/market operations BA wave |
| 34 | Michael Yen | Senior Contract Advisor at Shell; Houston | Weak for this role; no BA/ETRM/front-office visible | Keep filtered |
| 35 | Charles Smith | Career break; Houston | Weak/no evidence | Keep filtered |
| 36 | Nicole B. | Senior Settlements Analyst; Houston Utilities | Adjacent settlements/market ops, not BA/front-office | Add settlements analyst only as later wave |
| 37 | Karl Schroeder | Sr Endur Business Analyst at Shell; Houston | Very strong, but no Front Office exact phrase | Add relaxed Endur BA group |
| 38 | Sowmy Vijayaraghavan | ETRM; Business Architecture; Solution Architecture; Business/Technical Analysis; Houston | Strong, but not exact BA/Front Office | Add ETRM business architecture / technical analysis group |
| 39 | Sid Kotha | Portfolio Manager/SME; Market Risk and Credit Risk apps; Senior Business Analyst at Shell Trading; Greater Houston | Strong, but evidence is app/risk/SME, not Front Office | Add risk/credit apps + Shell Trading BA/SME group |
| 40 | Nasir Ali | Business Analyst II; Houston | BA/Houston, but no energy/ETRM/front-office visible | Needs energy/vendor qualifier |
| 41 | Jessie Jewell | Business Analyst at Shell; ETRM/Compliance; ETRM Endur; Houston | Very strong, but no Front Office exact | Add Shell + ETRM/Endur BA group |
| 42 | John S. Daly | Energy Trader; Risk Manager; Consultant; Houston | Trading/risk, but not BA/ETRM/tool visible | Add trader/risk manager only as adjacent market wave |
| 43 | Manisha Chugh | Business Architecture Associate Director; ETRM/Endur skills; United States | Strong skills, but location may not be Houston; not BA title | Add verification pass for location; add ETRM business architecture group |
| 44 | Aamir Nagaria | Director Commercial Applications at CVR Energy; Houston | Commercial apps energy leader, not BA/ETRM visible in title | Add commercial applications energy group |
| 45 | Israr Mandalvadi | Principal Consultant at Capco; ETRM/Endur; Houston | Strong, consultant not BA | Add Capco/ETRM/Endur consultant group |
| 46 | Willie Yao | Analytic Architect at Motiva; Houston | Architecture/analytics, not BA/ETRM visible | Medium/low unless analytic architect in energy apps wave |
| 47 | Moniz Mohammed | Trading & Risk Management Consultant at Capco; ETRM/Endur; Houston | Strong, consultant not BA | Add trading/risk management consultant + ETRM/Endur group |
| 48 | Kimberly Reese | Gas Scheduling Manager at ConocoPhillips; Houston | Adjacent gas scheduling, no BA/ETRM | Add gas scheduling only as market operations wave |
| 49 | Santhosh DS | Senior Manager at Sapient Global Markets; Senior Manager ETRM; ETRM/Endur; Houston | Strong, manager not BA | Add ETRM manager/global markets group |
| 50 | Anurag Mishra | Application Support/Market Data Management; Houston | Adjacent systems support, no ETRM/BA/front-office | Low/medium |
| 51 | Bhakta Ram | Energy commodities/capital markets trading and risk mgmt; ETRM/CTRM; OpenLink Endur; Houston | Very strong, but not BA/Front Office exact | Add OpenLink Endur trading/risk management group |
| 52 | Rick Lundquist | Energy Trading Systems and Integration Delivery; ETRM Implementation Business Analyst; Allegro; Houston | Very strong, but title starts trading systems/integration; old query lacked Allegro | Add Allegro + ETRM implementation BA group |
| 53 | Stephen Mink | Energy Markets Technologist; ETRM Architect; Risk Analytics; Greater Houston | Strong ETRM architect, not BA | Add ETRM architect/technologist group |
| 54 | Amyn Z | Commercial Operations; Compliance and Risk; Houston Utilities | Adjacent operations/risk; weak ETRM evidence | Low/medium market operations wave |
| 55 | Quentin Howard | Senior CTRM Support Engineer; Greater Houston | Strong CTRM, but support engineer not BA | Add CTRM support engineer group |
| 56 | Lily Wren | Corporate Senior Accountant; Houston; ETRM/Endur skills match | Likely weak/noisy; skills may match but role is accounting | Keep low unless accounting/settlements in scope |
| 57 | Warrick Franklin | Director Corporate Risk; United Energy Trading; Risk Manager; Houston | Strong risk/energy trading, but not BA/ETRM | Add corporate/market risk energy trading wave |
| 58 | Pranav Patel | Managing Partner; analytics consultant at Shell; ETRM/Endur skills; Houston | Consulting/analytics, not exact BA | Add Shell analytics consultant + ETRM/Endur group |
| 59 | Caleb M. | Trading Specialist; Senior Risk Analyst; Middle Office; Houston | Strong market ops/risk, but no BA/ETRM in title | Add middle office/risk analyst/trading specialist wave |
| 60 | Laurel Adams Lloyd | ETRM Software Consultant; ETRM/Endur; Greater Houston | Strong, consultant not BA | Add ETRM software consultant group |
| 61 | Howard Camp | ETRM Business Analyst; Senior Accountant; Volume and Finance Analyst; Houston | Very strong, but no Front Office exact | Add relaxed ETRM BA group |
| 62 | Balaji Gopalakrishnan | IT Supervisor App Dev and CreditRisk; Commercial Risk System Analyst; Houston | Strong commercial risk systems, not BA/front-office | Add commercial risk systems analyst group |
| 63 | Jerry Kahn | Expert ETRM developer/analyst; Lead ETRM Developer; Houston | Strong, developer/analyst not exact BA | Add ETRM developer/analyst group |
| 64 | Lindsay Wied | CX/resources industry; energy & utilities sales engineering; Houston | Weak for Front Office BA | Keep filtered |
| 65 | Baadal Vishal | ETRM/CTRM; Energy & Utilities digital transformation; Accenture; Houston | Strong, but transformation/consulting not exact BA | Add ETRM/CTRM transformation/program group |
| 66 | Wesley W. | Senior Manager Asset Management (Power); Day-Ahead Power Desk; Houston | Strong power desk/market operations, but not BA/ETRM | Add power desk / asset management market operations wave |
| 67 | Olumide Gboyega | Principal Consultant at Capco; ETRM/Endur; Houston | Strong, consultant not BA | Add Capco/ETRM/Endur consultant group |
| 68 | Rob Wheeler | Market/portfolio risk analyst; Senior Business Consultant/Project Manager; risk business analyst; Houston | Strong risk BA/consulting, but not Front Office exact | Add portfolio/market risk BA consultant group |
| 69 | Alec Wright | Program Manager/Product Manager; CTRM Program; KWA Analytics; Houston | Strong CTRM program manager, not BA | Add CTRM program/product manager group |
| 70 | Richard Poterek | ION RightAngle Functional/Technical Lead; Openlink/Solarc RightAngle Developer; Houston | Very strong, but old query lacked RightAngle and lead/developer terms | Add RightAngle/ION/Solarc functional technical lead group |
| 71 | Hubert Phillips | Endur BA/Tech; OpenLink Financial; Greater Houston | Very strong, but phrase is BA/Tech and consultant history | Add Endur BA/Tech + OpenLink Financial group |
| 72 | Prasanna Venkatesan | Senior Java Developer; Senior ETRM/Endur SME/Developer; Architect Business Analyst; Greater Houston | Strong, but developer/SME title; BA appears later | Add ETRM/Endur SME/developer/architect BA group |
| 73 | Chin Chong Tan | Senior Endur Developer; Shell; Houston | Strong Endur developer, not BA | Add Senior Endur Developer group |
| 74 | Mark McClure | Crude marketing accounting; gas pipeline operations accounting; volume settlement; Houston | Adjacent settlements/accounting, not BA/ETRM | Add only in market ops/accounting wave |
| 75 | Chiranjit Deka | Associate Manager at Accenture; Houston | Weak visible evidence | Keep filtered |
| 76 | Randy Garcia | Chief of Staff; IT/InfoSec Director; Houston | Weak visible evidence | Keep filtered |

## Pattern Improvements To Implement

### 1. Do not force `Business Analyst` in every query group

Current old behavior over-constrained discovery. The family should have multiple title lanes:

```text
Business Analyst / BA lane
Consultant / SME lane
Lead / Architect / Developer lane
Program / Product / Implementation Owner lane
Risk / Settlements / Middle Office lane
```

### 2. Add ETRM vendor/tool alternates

Add vendor/tool vocabulary as first-class search terms:

```text
Endur
OpenLink
Openlink
ION OpenLink
RightAngle
Allegro
Solarc
Aspect Enterprise
KWA Analytics
Capco
Sapient Global Markets
```

### 3. Add Front Office phrase variants

The photos show several profiles that express the same concept without the exact phrase `Front Office`.

Use:

```text
"Front Office"
"Front-Office"
"front-office technology"
"Front-Office Trading Desk"
"Front and Back Office"
"Trade Capture"
"Trading Systems"
"Commercial Applications"
"Business Applications"
```

### 4. Add commodity/trading domain lanes

Use domain terms that catch real Houston energy trading candidates:

```text
"Power Trading"
"Energy Trading"
"Gas Trading"
"Products & Gas Trading"
"Natural Gas"
LNG
Crude
"Commodity Trading"
"Energy Trading and Risk Management"
ETRM
CTRM
```

### 5. Add market-operations adjacent lanes as lower-priority waves

These should not be mixed with strongest ETRM/Endur queries, but they are useful for recall:

```text
"Middle Office"
Settlements
"Gas Scheduling"
"Trade Capture"
"Market Risk"
"Credit Risk"
"Portfolio Risk"
"Commercial Risk"
"Day-Ahead Power Desk"
```

### 6. Keep strict location, but add verification for name/profile evidence

Some photo profiles show only `United States` or `Greater Houston` depending on source view. For strict Houston searches:

- Accept direct evidence: `Houston`, `Greater Houston`, `Houston, Texas`.
- If a strong candidate has no location evidence in provider snippet, run a verification query by `name + profile + Houston`.
- Do not accept `United States` alone.

## Suggested Query Families

### Core BA

```text
site:linkedin.com/in/ ("Business Analyst" OR "Business Systems Analyst" OR "Technical Business Analyst" OR BA) (ETRM OR CTRM OR Endur OR OpenLink OR Openlink OR RightAngle OR Allegro) "Houston"
```

### ETRM Consultant / SME

```text
site:linkedin.com/in/ (Consultant OR SME OR Specialist OR Lead) (ETRM OR CTRM OR Endur OR OpenLink OR Openlink OR RightAngle OR Allegro) ("Energy Trading" OR Commodities OR Gas OR Power OR LNG OR Crude) "Houston"
```

### Front-office / Trade Capture

```text
site:linkedin.com/in/ ("Front Office" OR "Front-Office" OR "Front-Office Trading Desk" OR "Trade Capture" OR "Front and Back Office") (Endur OR OpenLink OR ETRM OR CTRM OR RightAngle OR Allegro) "Houston"
```

### Trading Systems / Commercial Applications

```text
site:linkedin.com/in/ ("Trading Systems" OR "Commercial Applications" OR "Business Applications" OR "Trading and Risk Management") (Energy OR Commodities OR Gas OR Power OR LNG OR Crude) "Houston"
```

### Market Operations / Risk

```text
site:linkedin.com/in/ ("Middle Office" OR Settlements OR "Gas Scheduling" OR "Market Risk" OR "Credit Risk" OR "Portfolio Risk") (Energy OR Trading OR Commodities OR Power OR Gas) "Houston"
```

## Priority Candidates We Should Have Found

Highest-confidence misses from the photo list:

1. Dhyan Pai
2. Gourav Roy
3. Piyush Srivastava
4. Viraj P
5. Krishna M.
6. Mosin A.
7. Alan Levine
8. Omar T.
9. Ashish Gupta
10. Brent Breaux
11. Karl Schroeder
12. Jessie Jewell
13. Israr Mandalvadi
14. Moniz Mohammed
15. Bhakta Ram
16. Rick Lundquist
17. Stephen Mink
18. Laurel Adams Lloyd
19. Howard Camp
20. Richard Poterek
21. Hubert Phillips
22. Prasanna Venkatesan
23. Chin Chong Tan

These are the candidates that show our current search logic is missing real market signal, not just noisy edge cases.
