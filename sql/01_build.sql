-- Executed by src/pipeline.py against SQLite 3.25+.
-- Money stays in integer GBP pence until presentation.
DROP VIEW IF EXISTS monthly_sales;
DROP VIEW IF EXISTS country_sales;
DROP VIEW IF EXISTS product_sales;
DROP VIEW IF EXISTS customer_orders;
DROP VIEW IF EXISTS country_monthly;
DROP TABLE IF EXISTS orders;
CREATE INDEX IF NOT EXISTS ix_ledger_invoice ON ledger(invoice);
CREATE INDEX IF NOT EXISTS ix_ledger_customer ON ledger(customer_id);
CREATE INDEX IF NOT EXISTS ix_ledger_month ON ledger(month);

CREATE TABLE orders AS
SELECT invoice, MIN(invoice_date) AS invoice_date, MIN(order_date) AS order_date,
       MIN(month) AS month, MAX(customer_id) AS customer_id, MAX(country) AS country,
       SUM(amount_pence) AS sales_pence, SUM(quantity) AS units, COUNT(*) AS lines
FROM ledger WHERE kind='sale' GROUP BY invoice;
CREATE UNIQUE INDEX ux_orders_invoice ON orders(invoice);
CREATE VIEW customer_orders AS SELECT * FROM orders WHERE customer_id IS NOT NULL;

CREATE VIEW monthly_sales AS
WITH money AS (
 SELECT month,
 SUM(CASE WHEN kind='sale' THEN amount_pence ELSE 0 END) AS gross_sales_pence,
 -SUM(CASE WHEN kind='return' THEN amount_pence ELSE 0 END) AS returns_pence,
 SUM(amount_pence) AS net_sales_pence,
 COUNT(DISTINCT CASE WHEN kind='sale' THEN invoice END) AS orders,
 COUNT(DISTINCT CASE WHEN kind='sale' THEN customer_id END) AS customers
 FROM ledger GROUP BY month
), growth AS (
 SELECT *, LAG(net_sales_pence) OVER (ORDER BY month) AS prior_net_sales_pence FROM money
)
SELECT *, CASE WHEN prior_net_sales_pence<>0 THEN 1.0*net_sales_pence/prior_net_sales_pence-1 END AS mom_growth
FROM growth ORDER BY month;

CREATE VIEW country_sales AS
SELECT country, SUM(CASE WHEN kind='sale' THEN amount_pence ELSE 0 END) AS gross_sales_pence,
       -SUM(CASE WHEN kind='return' THEN amount_pence ELSE 0 END) AS returns_pence,
       SUM(amount_pence) AS net_sales_pence,
       COUNT(DISTINCT CASE WHEN kind='sale' THEN invoice END) AS orders,
       COUNT(DISTINCT CASE WHEN kind='sale' THEN customer_id END) AS customers
FROM ledger GROUP BY country ORDER BY net_sales_pence DESC;

CREATE VIEW country_monthly AS
SELECT country,month,
 SUM(CASE WHEN kind='sale' THEN amount_pence ELSE 0 END) AS gross_sales_pence,
 -SUM(CASE WHEN kind='return' THEN amount_pence ELSE 0 END) AS returns_pence,
 SUM(amount_pence) AS net_sales_pence,
 COUNT(DISTINCT CASE WHEN kind='sale' THEN invoice END) AS orders
FROM ledger GROUP BY country,month ORDER BY country,month;

CREATE VIEW product_sales AS
SELECT stock_code, MAX(description) AS description,
 SUM(CASE WHEN kind='sale' THEN amount_pence ELSE 0 END) AS gross_sales_pence,
 -SUM(CASE WHEN kind='return' THEN amount_pence ELSE 0 END) AS returns_pence,
 SUM(amount_pence) AS net_sales_pence,
 SUM(CASE WHEN kind='sale' THEN quantity ELSE 0 END) AS units_sold,
 -SUM(CASE WHEN kind='return' THEN quantity ELSE 0 END) AS units_returned
FROM ledger GROUP BY stock_code ORDER BY gross_sales_pence DESC;
