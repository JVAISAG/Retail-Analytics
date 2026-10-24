# Portfolio description and interview preparation

## Resume bullets (use after reviewing and understanding the implementation)
- Built a reproducible Python/SQL retail analytics pipeline processing 1,067,371 transaction records, with documented cleaning rules and 9 reconciliation checks.
- Analyzed GBP 18.93M in historical net merchandise sales and segmented 5,852 identified buyers using RFM scores, with cohort retention analysis and an interactive offline dashboard.
- Tested the association between first observed order value and 90-day repeat purchasing across 5,256 eligible customers, reporting confidence intervals and controlling follow-up length.

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
