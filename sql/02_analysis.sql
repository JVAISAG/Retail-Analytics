-- Explore data/processed/retail.sqlite with any SQLite client.
-- 1. Monthly trend, window function and explicitly partial final month.
SELECT month, gross_sales_pence/100.0 AS gross_sales_gbp,
       net_sales_pence/100.0 AS net_sales_gbp, orders,
       gross_sales_pence/100.0/orders AS average_order_value_gbp, mom_growth
FROM monthly_sales ORDER BY month;

-- 2. Product revenue ranking with a cumulative contribution (Pareto analysis).
WITH ranked AS (
 SELECT stock_code, description, gross_sales_pence,
        DENSE_RANK() OVER (ORDER BY gross_sales_pence DESC) AS revenue_rank,
        SUM(gross_sales_pence) OVER () AS total_sales,
        SUM(gross_sales_pence) OVER (ORDER BY gross_sales_pence DESC,stock_code ROWS UNBOUNDED PRECEDING) AS cumulative_sales
 FROM product_sales
)
SELECT *, 1.0*cumulative_sales/total_sales AS cumulative_sales_share
FROM ranked ORDER BY revenue_rank,stock_code LIMIT 20;

-- 3. Customer dimension joined to purchase facts, aggregated before joining.
SELECT r.segment, COUNT(DISTINCT o.customer_id) AS customers,
       COUNT(*) AS orders, SUM(o.sales_pence)/100.0 AS gross_sales_gbp
FROM customer_orders o JOIN rfm_customers r ON r.customer_id=o.customer_id
GROUP BY r.segment ORDER BY gross_sales_gbp DESC;

-- 4. Cohort retention: NULL is not yet observable, zero is observed with no return.
SELECT cohort,age,cohort_customers,active_customers,retention
FROM cohort_retention ORDER BY cohort,age;

-- 5. Monetary prioritization within a customer segment.
SELECT customer_id,recency_days,frequency,monetary_gbp,rfm_score
FROM rfm_customers WHERE segment='At risk'
ORDER BY monetary_pence DESC LIMIT 20;

-- 6. Quality check for invoice-header ambiguity; expected zero rows.
SELECT invoice FROM ledger WHERE kind='sale' GROUP BY invoice
HAVING COUNT(DISTINCT country)>1 OR COUNT(DISTINCT customer_id)>1
    OR COUNT(DISTINCT order_date)>1;
