"""Generate narrative and the offline dashboard from calculated results."""
import json


def write_deliverables(root, s, data):
    study=s['study']
    high,low=study['groups']
    top=data['countries'][0]
    top_share=top['gross_sales_pence']/(s['gross_sales_gbp']*100)
    segments={x['segment']:x for x in data['segments']}
    risk=segments.get('At risk',{'customers':0,'sales_share':0})
    complete=[x for x in data['monthly'] if x['month']!=s['period_end'][:7]]
    peak=max(complete,key=lambda x:x['net_sales_pence'])
    report=f"""# Retail sales and customer retention: findings

## Decision
Where should a retail manager focus customer retention and sales monitoring?

## Scope and definitions
Analysis covers **{s['period_start'][:10]} to {s['period_end'][:10]}**. All monetary values are GBP.
The final month is partial and is excluded from the peak full-month comparison below.
This is a historical portfolio case study, not a description of the retailer's current business.
Gross sales include retained positive merchandise lines, including anonymous purchases.
Returns are the absolute value of retained negative merchandise lines; net sales = gross sales - returns.
These are transaction-value measures, not audited accounting revenue or profit. Shipping, fees and nonstandard stock codes are excluded.

## Findings and actions
1. **Sales scale:** GBP {s['gross_sales_gbp']:,.2f} gross sales, GBP {s['returns_gbp']:,.2f} returns and GBP {s['net_sales_gbp']:,.2f} net sales across {s['orders']:,} positive-sale invoices. Average gross order value is GBP {s['average_order_value_gbp']:,.2f}. Monitor gross and net separately so return activity is visible.
2. **Market concentration:** {top['country']} contributes {top_share:.1%} of gross sales. Prioritize market-level tracking and investigate concentration risk before recommending geographic expansion; acquisition costs are unavailable.
3. **Observed repeat behavior:** {s['repeat_customers']:,} of {s['identified_customers']:,} identified buyers placed at least two orders ({s['repeat_customer_rate']:.1%}). This full-history measure gives earlier buyers more follow-up; use the 90-day study for an equal follow-up comparison.
4. **Retention review list:** {risk['customers']:,} buyers are classified as At risk at {s['snapshot_date']}, accounting for {risk['sales_share']:.1%} of historical identified-customer gross sales. Review the highest-value buyers first and design a randomized outreach pilot. Their historical sales are not predicted recoverable revenue.
5. **Peak observed complete month:** {peak['month']} generated GBP {peak['net_sales_pence']/100:,.2f} net sales. Plan a demand review around the observed pattern, while recognizing that roughly two years of history cannot establish a stable seasonal effect.

## Statistical case study
**Question:** {study['question']}

{study['eligible_customers']:,} customers have at least 90 days of observation after their first observed order; {study['excluded_recent_customers']:,} newer customers are excluded.
The grouping threshold is GBP {study['first_order_median_gbp']:,.2f}, the eligible population's median first-order value.

| First observed order | Customers | Repeat buyers within 90 days | Rate | 95% Wilson CI |
|---|---:|---:|---:|---:|
| {high['group']} | {high['customers']:,} | {high['repeat_customers']:,} | {high['repeat_rate']:.1%} | {high['ci_low']:.1%} to {high['ci_high']:.1%} |
| {low['group']} | {low['customers']:,} | {low['repeat_customers']:,} | {low['repeat_rate']:.1%} | {low['ci_low']:.1%} to {low['ci_high']:.1%} |

Difference (above minus at/below median): **{study['difference']*100:.2f} percentage points**, 95% difference CI [{study['difference_ci_low']*100:.2f}, {study['difference_ci_high']*100:.2f}]. Two-sided two-proportion z = {study['z_statistic']:.3f}, p = {study['p_value']:.4g}, alpha = 0.05.
The test {'rejects' if study['p_value']<0.05 else 'does not reject'} equal group rates at the stated threshold. The effect size and interval matter alongside the p-value.

{study['limitations']}
The test treats customer outcomes as independent. The median split is descriptive and loses information about order size.
Recommend a future randomized experiment to test an intervention; do not claim that increasing basket size causes retention.

## Cleaning and reconciliation
{s['raw_rows']:,} source rows become {s['retained_rows']:,} retained sale/return lines. See data/processed/data_quality.csv for mutually exclusive exclusions, and excluded_stock_codes.csv for codes omitted by the merchandise rule.
Anonymous gross sales total GBP {s['unidentified_sales_gbp']:,.2f}; those sales remain in sales KPIs but cannot support customer-level retention or RFM.
Exact normalized duplicate lines are removed under an explicit assumption that they are duplicate records. The source has no line ID; identical lines could sometimes be legitimate. The raw workbook is preserved for sensitivity analysis.
Returns remain on their recorded date and are not matched to original purchases. Monetary calculations preserve the source unit price, multiply by integer quantity using decimal arithmetic, then round the complete line to pennies using ties-to-even.
The executed pipeline passes {s['validation']['reconciliations_passed']} reconciliation checks, plus SQLite integrity ({s['validation']['sqlite_integrity']}).

## Cohorts and RFM
Cohorts use the month of first **observed** identified purchase. Retention is customers buying in month N / cohort size; it is not cumulative retention. Unobservable cells are blank, and the incomplete final month is excluded.
RFM uses positive purchases only: recency in calendar days at the fixed snapshot, frequency as distinct invoices, monetary as gross purchases. Each score is ceil(5 × average percentile rank), with reverse ranking for recency. Ties share a score; groups need not have equal sizes. Segment names use R/F rules; M ranks value within them. See docs/METHODOLOGY.md.

## Source and reproducibility
Chen, D. (2012), Online Retail II, UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D . CC BY 4.0.
Source page: {s['source_url']}
Source SHA-256: `{s['source_sha256']}`.
Run `python src/pipeline.py` to regenerate the analysis, dashboard and report, then `python -m unittest discover -s tests -v`.
"""
    (root/'reports/FINDINGS.md').write_text(report,encoding='utf-8')
    template=(root/'src/dashboard_template.html').read_text(encoding='utf-8')
    escaped=json.dumps(data).replace('</','<\\/')
    (root/'dashboard.html').write_text(template.replace('__DATA_JSON__',escaped),encoding='utf-8')
    resume=f"""# Portfolio description and interview preparation

## Resume bullets (use after reviewing and understanding the implementation)
- Built a reproducible Python/SQL retail analytics pipeline processing {s['raw_rows']:,} transaction records, with documented cleaning rules and {s['validation']['reconciliations_passed']} reconciliation checks.
- Analyzed GBP {s['net_sales_gbp']/1e6:.2f}M in historical net merchandise sales and segmented {s['identified_customers']:,} identified buyers using RFM scores, with cohort retention analysis and an interactive offline dashboard.
- Tested the association between first observed order value and 90-day repeat purchasing across {study['eligible_customers']:,} eligible customers, reporting confidence intervals and controlling follow-up length.

Do not claim that the project increased sales, improved retention, or was deployed for a real client. Add Power BI to these bullets only after building and checking the native report using powerbi/BUILD_GUIDE.md.

## Explain these decisions in an interview
1. Why anonymous purchases belong in sales totals but not customer retention.
2. Why returns are retained and gross sales differ from net sales.
3. Why invoice count, line count and customer count differ.
4. How CTEs, window functions and pre-aggregated joins avoid double-counting.
5. How incomplete follow-up can bias repeat rates and why the study uses 90 days.
6. Why first observed purchase is not necessarily customer acquisition.
7. Why RFM ties share scores and segment sizes are unequal.
8. Why a statistically significant association is not a causal business impact.
9. What you would add with cost, inventory, acquisition-channel and experiment data.
"""
    (root/'reports/PORTFOLIO_NOTES.md').write_text(resume,encoding='utf-8')
