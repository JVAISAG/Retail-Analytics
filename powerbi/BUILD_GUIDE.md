# Build the native Power BI report

This folder contains a prepared import query, DAX definitions, theme and visual specification. A `.pbix` has not been created or executed in Power BI Desktop. Python/SQL results and the offline/Excel dashboards are completed separately. These Power BI materials require final import and validation in Desktop.

## 1. Load the tables

1. Extract the complete project to a local folder.
2. In Power BI Desktop, create a blank query. Paste Ledger.pq into Advanced Editor. Replace ProjectRoot with the extracted project folder. Name the query **Ledger**. The query decompresses the supplied gzip file before parsing CSV.
3. Import data/processed/rfm_customers.csv as **Customers**, with customer_id and rfm_score as text; frequency, monetary_pence and scores as whole numbers.
4. Import data/processed/cohort_retention.csv as **Cohorts**. cohort is text, age and observed whole numbers, retention decimal. Keep blanks blank.
5. Disable automatic relationships for these imported tables. Customers and Cohorts are fixed-snapshot analyses and intentionally stay disconnected from Ledger in this design. Do not sum pre-aggregated totals across overlapping fact tables.

## 2. Create measures and the date relationship

Add each measure from Measures.dax individually. Create Calendar as a calculated table. Create a one-to-many, single-direction relationship from Calendar[Date] to Ledger[order_date]. Mark Calendar as the date table. Sort Calendar[Month] by Calendar[Month Sort].

Format monetary measures as GBP, counts as whole numbers and rate measures as percentages. Do not sum customer IDs or invoice numbers.

## 3. Report layout

Use a 16:9 page and import theme.json.

**Sales overview:**

- Top row: Net Sales GBP, Gross Sales GBP, Orders, Average Order Value GBP.
- Slicers: Calendar[Date] range and Ledger[country].
- Line chart: Calendar[Month] on X; Gross Sales GBP and Net Sales GBP on Y.
- Sorted bar chart: Ledger[country] and Net Sales GBP, top 6 by Net Sales GBP.
- Product table: Ledger[stock_code], Gross Sales GBP, Returns GBP and Net Sales GBP. Avoid grouping only by changing descriptions.
- Monthly table: Calendar[Month], Gross Sales GBP, Returns GBP, Net Sales GBP, Orders, Average Order Value GBP.
- Add a visible note that December 2011 is partial. All figures are merchandise transaction values in GBP.

**Customers and retention:**

- Cards: Snapshot Buyers, Snapshot Repeat Buyers, Snapshot Repeat Buyer Rate.
- Bar/table: Customers[segment] and Snapshot Gross Sales GBP; show buyer counts alongside value.
- Customer review table: customer_id, recency_days, frequency, monetary_gbp, rfm_score and segment. Sort monetary_gbp descending.
- Cohort matrix: Cohorts[cohort] rows, Cohorts[age] columns, Cohort Retention values. Turn off row and column totals. Apply a single-color percentage scale. Unobserved cells must stay blank, rather than displaying 0%.
- State the fixed RFM snapshot date from summary.json. Do not synchronize the sales slicers to this page: these tables represent the full-history snapshot.
- Add a text box with the study rates, difference CI and caveat from reports/FINDINGS.md. It is a Python-computed statistical result, not a dynamic DAX experiment.

## 4. Validate before sharing

Clear all slicers. Compare the money/count cards to data/processed/summary.json. Compare a single month's country selection to country_monthly.csv, and a product total to product_sales.csv. Check that returns reduce net sales and that identifiers are text. Check that cohort blanks remain blank and snapshot cards remain explicitly fixed-scope.

Save the validated report as Retail_Analytics.pbix. Claim Power BI project experience on your resume after completing and understanding this step.

## Microsoft references

- Binary.Decompress, including Compression.GZip: https://learn.microsoft.com/en-us/powerquery-m/binary-decompress
- Csv.Document: https://learn.microsoft.com/en-us/powerquery-m/csv-document
- CALCULATE: https://learn.microsoft.com/en-us/dax/calculate-function-dax
- DISTINCTCOUNT: https://learn.microsoft.com/en-us/dax/distinctcount-function-dax
- DIVIDE: https://learn.microsoft.com/en-us/dax/divide-function-dax
