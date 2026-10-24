# Excel summary refresh

The delivered workbook contains aggregate results, not all one million source rows. The complete source, cleaned line-level data and database remain in data/.

1. Regenerate results with `python src/pipeline.py`.
2. Replace the corresponding source values in the workbook's Monthly, Segments, Cohorts and Quality sheets from the generated CSV/JSON files. Keep the existing headers and column order.
3. Preserve calculated AOV, growth, shares and retention formulas. For changed row counts, extend or shorten tables and chart source ranges.
4. Refresh the fixed study inputs from summary.json, including sample sizes and confidence intervals. Its statistical test is computed in Python, not recomputed by Excel.
5. Recalculate Excel and reconcile the Overview KPIs to summary.json. The unique-buyer/full-history repeat figures must use the supplied whole-period counts, not sums of monthly unique counts.

The workbook is a historical snapshot with formulas over its supplied inputs. It has no automatic external-data connection, macros, or claim of live refresh. The HTML dashboard updates automatically when the Python pipeline runs.
