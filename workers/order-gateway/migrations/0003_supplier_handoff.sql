CREATE TABLE supplier_handoffs (
  order_id TEXT PRIMARY KEY REFERENCES orders(order_id),
  claimed_at TEXT NOT NULL,
  supplier_reference TEXT UNIQUE
);
