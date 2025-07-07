WITH
  sales_summary AS (
    SELECT
      SUM(t."transaction_amount")                                        AS "total_sales",
      COUNT(DISTINCT t."order_id")                                       AS "transactions",
      ROUND(AVG(t."transaction_amount")::numeric, 2)                     AS "avg_transaction_value"
    FROM "transactions" t
    WHERE (t."date_time"::date) = CURRENT_DATE - 1
  ),

  commission_summary AS (
    SELECT
      SUM(o."quantity" * b."commission")                                 AS "total_commission"
    FROM "orders" o
    JOIN "products" p       ON o."product_id"   = p."id"
    JOIN "batch" b          ON p."batch_number" = b."id"
    JOIN "transactions" t   ON o."order_id"     = t."order_id"
    WHERE (t."date_time"::date) = CURRENT_DATE - 1
  ),

  top_products AS (
    SELECT
      p."product_name",
      SUM(o."quantity")                                                AS "units_sold"
    FROM "orders" o
    JOIN "products" p     ON o."product_id" = p."id"
    JOIN "transactions" t ON o."order_id"   = t."order_id"
    WHERE (t."date_time"::date) = CURRENT_DATE - 1
    GROUP BY p."product_name"
    ORDER BY "units_sold" DESC
    LIMIT 5
  ),

  top_customers AS (
    SELECT
      c."name"                                                          AS "customer_name",
      SUM(t."transaction_amount")                                       AS "amount_spent"
    FROM "transactions" t
    JOIN "customers" c    ON t."customer_id" = c."id"
    WHERE (t."date_time"::date) = CURRENT_DATE - 1
    GROUP BY c."name"
    ORDER BY "amount_spent" DESC
    LIMIT 5
  ),

  employee_performance AS (
    SELECT
      e."name"                                                          AS "employee_name",
      COUNT(t."order_id")                                               AS "transactions_handled"
    FROM "transactions" t
    JOIN "employees" e    ON t."employee_id" = e."id"
    WHERE (t."date_time"::date) = CURRENT_DATE - 1
    GROUP BY e."name"
    ORDER BY "transactions_handled" DESC
    LIMIT 5
  ),

  low_stock AS (
    SELECT
      p."product_name",
      SUM(b."remaining")                                                AS "stock_remaining",
      p."reorder_level"
    FROM "products" p
    JOIN "batch" b      ON p."batch_number" = b."id"
    GROUP BY p."product_name", p."reorder_level"
    HAVING SUM(b."remaining") < p."reorder_level"
  ),

  expiring_batches AS (
    SELECT
      b."id"                                                            AS "batch_id",
      p."product_name",
      b."expiry",
      b."remaining"
    FROM "batch" b
    JOIN "products" p ON p."batch_number" = b."id"
    WHERE b."expiry"
          BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '7 days')
  )

SELECT json_build_object(
  'sales_summary',         (SELECT row_to_json(ss)   FROM sales_summary ss),
  'commission_summary',    (SELECT row_to_json(cs)   FROM commission_summary cs),
  'top_products',          (SELECT json_agg(tp)      FROM top_products tp),
  'top_customers',         (SELECT json_agg(tc)      FROM top_customers tc),
  'employee_performance',  (SELECT json_agg(ep)      FROM employee_performance ep),
  'low_stock',             (SELECT json_agg(ls)      FROM low_stock ls),
  'expiring_batches',      (SELECT json_agg(eb)      FROM expiring_batches eb)
) AS daily_insights;
