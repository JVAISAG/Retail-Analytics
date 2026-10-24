# Validation record

- Full source: 1,067,371 rows across both original worksheets.
- Pipeline: 9 reconciliation checks, plus SQLite integrity `ok`.
- Python: 12 tests pass, including returns, anonymous purchases, duplicate handling, sub-penny prices, cohort censoring, 90-day boundaries, RFM ties, invoice headers, lineage and joins.
- SQL: all 6 queries in sql/02_analysis.sql executed successfully. The invoice-ambiguity query returned zero rows. See sql_query_results.json.
- Dashboard: DOM-only JavaScript checks passed for totals, country/date filters against an independent SQL query, a single-month range, reset, tabs, customer/cohort counts and quality metadata. No external scripts or stylesheet dependencies. See dashboard_validation.json.
- Excel: all 5 sheets visually reviewed; formula scan returned no errors. Editing a monthly input recalculated the overview, then the original input was restored. Saved workbook values agree with Python; native chart references and series colors are preserved.

## Limits of verification

The HTML dashboard's rendered appearance was not verified in a browser. Local browser preview was unavailable in this environment; the DOM tests check functional behavior rather than pixel layout. Excel was rendered and verified through the authoring engine and inspected after export, not opened in the native Excel application. Power BI files are prepared build materials; no `.pbix` was created or executed in Power BI Desktop.

The documented duplicate and merchandise-code assumptions are analytical choices, not proof that excluded lines are incorrect. The statistical study reports observational association, not intervention uplift.
