# Data dictionary

All CSVs use UTF-8, comma delimiters and a header. Monetary integer columns ending `_pence` use GBP pennies. Columns ending `_gbp` use GBP pounds. Identifiers should be imported as text. Rates are fractions (0.25 = 25%). The SQLite database contains the same logical tables.

| File/table | Grain | Important columns |
|---|---|---|
| ledger.csv.gz / ledger | Retained original invoice line | source_sheet, source_row, invoice, stock_code, description, quantity (signed), invoice_date (timestamp), order_date, month, unit_price_gbp (source precision), amount_pence (signed rounded line value), customer_id (nullable), country, kind (sale/return) |
| orders.csv / orders | Positive-sale invoice | invoice, invoice_date, order_date, month, customer_id, country, sales_pence, units, lines |
| customer_orders.csv / customer_orders | Identified positive-sale invoice | Same as orders, with nonmissing customer_id |
| monthly_sales.csv / monthly_sales | Calendar month | gross_sales_pence, returns_pence (positive deduction), net_sales_pence, orders, customers, prior_net_sales_pence, mom_growth (NULL first month) |
| country_sales.csv / country_sales | Country | country, gross_sales_pence, returns_pence, net_sales_pence, orders, customers |
| country_monthly.csv / country_monthly | Country × month | country, month, gross_sales_pence, returns_pence, net_sales_pence, orders |
| product_sales.csv / product_sales | Stock code | stock_code, representative description, gross_sales_pence, returns_pence, net_sales_pence, units_sold, units_returned |
| rfm_customers.csv / rfm_customers | Identified buyer | customer_id, first_purchase, last_purchase, recency_days, frequency, monetary_pence, monetary_gbp, r_score, f_score, m_score, rfm_score (text), segment |
| customer_segments.csv / customer_segments | R/F segment | segment, customers, sales_pence (gross identified purchases), orders, customer_share, sales_share |
| cohort_retention.csv / cohort_retention | Observed cohort × age 0..12 | cohort, age (months), cohort_customers, active_customers (nullable), retention (nullable), observed (0/1) |
| repeat_study_customers.csv / repeat_study_customers | Buyer with 90-day follow-up | customer_id, first_invoice, first_date, first_sales_pence, repeat90 (boolean), group |
| data_quality.csv | Row disposition | disposition, rows; mutually exclusive and exhaustive |
| excluded_stock_codes.csv | Excluded nonstandard stock code | stock_code, rows |
| summary.json | Whole-analysis metadata | exact period, source hash, sales KPIs, quality, statistical study and validation |
| dashboard_data.json | Dashboard payload | summary and full-scope aggregate arrays; product array includes top 20 only |

Orders count invoices with sale lines. Customer counts omit missing IDs. Returns may refer to a purchase outside the observation period. A product's returns-to-sales ratio is therefore a period activity measure, not a matched purchase return rate.
