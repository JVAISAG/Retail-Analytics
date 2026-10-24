# Methodology

## Source and grain

The original workbook has two worksheets. Every source line receives a worksheet name and original Excel row number. One row represents an invoice line, not an order or customer. Workbook bytes and SHA-256 are preserved in the analysis metadata. Source IDs and currencies are not inferred from the user's location.

## Cleaning order

Each source row receives exactly one disposition using the following priority:

1. **Duplicate:** remove subsequent exact matches on normalized invoice, stock code, description, quantity, date, unit price, customer and country. Source provenance is excluded from comparison so a repeated source line is still detected. Identical legitimate lines cannot be ruled out without line IDs; this is an assumption.
2. **Invalid required value:** blank invoice or stock code, invalid date, nonfinite price or quantity, fractional quantity, or extreme price outside the defined guard.
3. **Non-merchandise code:** stock code does not match five digits followed by zero to two ASCII letters. This excludes postage, fees, adjustments and any nonstandard product identifiers. All excluded codes are exported for review; the rule may also omit legitimate nonstandard items.
4. **Nonpositive price:** unit price <= 0. Free products do not contribute to paid merchandise sales in this analysis.
5. **Zero quantity.**
6. **Positive cancellation:** invoice starts C but quantity is positive; excluded as inconsistent.
7. **Retained:** positive quantity is a sale; negative quantity is a return/negative adjustment. Negative quantities are not assumed to be fraud or discarded as ordinary outliers.

Customer ID is normalized to nullable integer text. Missing/invalid customer IDs remain anonymous. Blank country is Unknown. Source descriptions are trimmed, not used to infer categories. Stock-code spellings are preserved.

Preserve the source unit price, including sub-penny values. Multiply its decimal string representation by integer quantity, then round the complete line to integer GBP pennies with decimal ties-to-even rounding. This avoids premature unit-price rounding and cumulative floating-point summation error. Outlying valid transactions remain; wholesale purchases and large returns can be real. No winsorization is applied.

## Sales

Gross = sum positive merchandise amounts. Returns = absolute sum negative merchandise amounts. Net = gross - returns. AOV = gross / distinct sale invoices. Negative invoices are not positive-sale orders. Product descriptions use one representative lexicographic maximum per stock code, because names vary; stock code is the product key. Returns are recorded in the period in which they occur, without attempting unverifiable links to original purchases.

Orders aggregate retained sale lines before joining to the customer table. A validation query checks that each invoice has at most one country, identified customer and date. Monthly customer counts are not summed across months to estimate unique buyers.

## RFM

Use identified positive-sale invoices over the full observed period. Snapshot is the day after the maximum retained transaction date. Recency counts calendar days from the last purchase date. Frequency counts distinct invoices. Monetary value sums gross purchase pennies; returns do not alter RFM value in this implementation.

Scores are `ceil(5 * average percentile rank)`, clipped to 1..5. Recency ranking is reversed so recently active buyers score higher. Ties receive identical scores and groups are not guaranteed equal sizes.

Rules are applied in this order:

| Rule | Segment |
|---|---|
| R >= 4 and F >= 4 | Champions |
| R >= 4 and F >= 2 | Recent repeat buyers |
| R >= 4 otherwise | Recent low-frequency buyers |
| R <= 2 and F >= 3 | At risk |
| R <= 2 and F <= 2 | Hibernating |
| Otherwise | Needs attention |

M ranks monetary value within the R/F segments. These labels are heuristics, not learned churn probabilities. Suggested actions: protect service for Champions; review repeat demand for Recent repeat buyers; test onboarding for Recent low-frequency buyers; investigate high historical spend among At risk buyers; test low-cost reactivation for Hibernating buyers. No recovery amounts are estimated.

## Cohorts

The first observed purchase month defines the cohort. Cohort size is unique identified buyers in month 0. Retention at age N is buyers purchasing in month N / original cohort size. It is not cumulative. A buyer may return after a gap. Observed months with no repeat activity are zero. Unobserved months are NULL, never zero. The final month is excluded unless the extract reaches its calendar month end. The source may begin after a buyer's true first purchase.

## Statistical study

First observed order per buyer is sorted by timestamp then invoice ID. Include buyers only when this date is at least 90 days before the last transaction. A repeat is another positive-sale invoice at a later timestamp within 90 days. Same-timestamp invoices do not count as a later purchase.

The median eligible first-order amount defines Above median and At or below median groups; ties stay in the latter group. H0: equal population repeat rates. Use a two-sided pooled two-proportion z-test at alpha=0.05. Group CIs use Wilson's method. Difference CI uses the unpooled normal approximation. Source code records both numerators, denominators, z, p and intervals. Check sample sizes before using this approach on a different dataset.

This is an unadjusted observational analysis. Customer outcomes are treated as independent. Country, season, wholesale status and pre-observation purchasing can confound the association. A median split loses information. The result is not a causal estimate; confirm any proposed intervention with a randomized experiment.

## Outputs and refresh scope

Python refreshes the SQLite database, CSV/gzip files, JSON, findings, portfolio notes and offline dashboard. The Excel workbook is a separate summary snapshot with live formulas and native charts over supplied aggregate tables; it does not automatically read new pipeline files. Power BI artifacts are build materials rather than a pre-authored `.pbix`.
