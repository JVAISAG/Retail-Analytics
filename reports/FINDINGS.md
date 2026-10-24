# Retail sales and customer retention: findings

## Decision
Where should a retail manager focus customer retention and sales monitoring?

## Scope and definitions
Analysis covers **2009-12-01 to 2011-12-09**. All monetary values are GBP.
The final month is partial and is excluded from the peak full-month comparison below.
This is a historical portfolio case study, not a description of the retailer's current business.
Gross sales include retained positive merchandise lines, including anonymous purchases.
Returns are the absolute value of retained negative merchandise lines; net sales = gross sales - returns.
These are transaction-value measures, not audited accounting revenue or profit. Shipping, fees and nonstandard stock codes are excluded.

## Findings and actions
1. **Sales scale:** GBP 19,642,692.15 gross sales, GBP 716,425.97 returns and GBP 18,926,266.18 net sales across 39,516 positive-sale invoices. Average gross order value is GBP 497.08. Monitor gross and net separately so return activity is visible.
2. **Market concentration:** United Kingdom contributes 85.5% of gross sales. Prioritize market-level tracking and investigate concentration risk before recommending geographic expansion; acquisition costs are unavailable.
3. **Observed repeat behavior:** 4,234 of 5,852 identified buyers placed at least two orders (72.4%). This full-history measure gives earlier buyers more follow-up; use the 90-day study for an equal follow-up comparison.
4. **Retention review list:** 709 buyers are classified as At risk at 2011-12-10, accounting for 8.9% of historical identified-customer gross sales. Review the highest-value buyers first and design a randomized outreach pilot. Their historical sales are not predicted recoverable revenue.
5. **Peak observed complete month:** 2011-11 generated GBP 1,427,121.25 net sales. Plan a demand review around the observed pattern, while recognizing that roughly two years of history cannot establish a stable seasonal effect.

## Statistical case study
**Question:** Is first observed order size associated with another purchase within 90 days?

5,256 customers have at least 90 days of observation after their first observed order; 596 newer customers are excluded.
The grouping threshold is GBP 291.56, the eligible population's median first-order value.

| First observed order | Customers | Repeat buyers within 90 days | Rate | 95% Wilson CI |
|---|---:|---:|---:|---:|
| Above median | 2,628 | 1,383 | 52.6% | 50.7% to 54.5% |
| At or below median | 2,628 | 1,062 | 40.4% | 38.6% to 42.3% |

Difference (above minus at/below median): **12.21 percentage points**, 95% difference CI [9.54, 14.89]. Two-sided two-proportion z = 8.877, p = 6.873e-19, alpha = 0.05.
The test rejects equal group rates at the stated threshold. The effect size and interval matter alongside the p-value.

Observational association; no causal effect. First observed order may not be acquisition. Country, season and wholesale mix may confound results. Same-timestamp invoices do not count as a subsequent purchase.
The test treats customer outcomes as independent. The median split is descriptive and loses information about order size.
Recommend a future randomized experiment to test an intervention; do not claim that increasing basket size causes retention.

## Cleaning and reconciliation
1,067,371 source rows become 1,021,128 retained sale/return lines. See data/processed/data_quality.csv for mutually exclusive exclusions, and excluded_stock_codes.csv for codes omitted by the merchandise rule.
Anonymous gross sales total GBP 2,574,124.18; those sales remain in sales KPIs but cannot support customer-level retention or RFM.
Exact normalized duplicate lines are removed under an explicit assumption that they are duplicate records. The source has no line ID; identical lines could sometimes be legitimate. The raw workbook is preserved for sensitivity analysis.
Returns remain on their recorded date and are not matched to original purchases. Monetary calculations preserve the source unit price, multiply by integer quantity using decimal arithmetic, then round the complete line to pennies using ties-to-even.
The executed pipeline passes 9 reconciliation checks, plus SQLite integrity (ok).

## Cohorts and RFM
Cohorts use the month of first **observed** identified purchase. Retention is customers buying in month N / cohort size; it is not cumulative retention. Unobservable cells are blank, and the incomplete final month is excluded.
RFM uses positive purchases only: recency in calendar days at the fixed snapshot, frequency as distinct invoices, monetary as gross purchases. Each score is ceil(5 × average percentile rank), with reverse ranking for recency. Ties share a score; groups need not have equal sizes. Segment names use R/F rules; M ranks value within them. See docs/METHODOLOGY.md.

## Source and reproducibility
Chen, D. (2012), Online Retail II, UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D . CC BY 4.0.
Source page: https://archive.ics.uci.edu/dataset/502/online+retail+ii
Source SHA-256: `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
Run `python src/pipeline.py` to regenerate the analysis, dashboard and report, then `python -m unittest discover -s tests -v`.
