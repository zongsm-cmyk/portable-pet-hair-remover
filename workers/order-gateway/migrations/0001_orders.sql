PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS checkout_intents (
  order_id TEXT PRIMARY KEY,
  paypal_order_id TEXT UNIQUE,
  country TEXT NOT NULL CHECK(country IN ('US','GB')),
  items_json TEXT NOT NULL,
  total_cents INTEGER NOT NULL CHECK(total_cents > 0),
  state TEXT NOT NULL DEFAULT 'creating',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS orders (
  order_id TEXT PRIMARY KEY REFERENCES checkout_intents(order_id),
  paypal_order_id TEXT NOT NULL UNIQUE,
  paypal_capture_id TEXT NOT NULL UNIQUE,
  customer_name TEXT NOT NULL,
  email TEXT NOT NULL,
  shipping_address TEXT NOT NULL,
  items_json TEXT NOT NULL,
  cj_sku TEXT NOT NULL,
  cj_variant_id TEXT NOT NULL,
  quantity INTEGER NOT NULL CHECK(quantity > 0),
  total_paid_usd TEXT NOT NULL,
  payment_status TEXT NOT NULL CHECK(payment_status = 'COMPLETED'),
  fulfillment_status TEXT NOT NULL DEFAULT 'unfulfilled',
  tracking_number TEXT,
  tracking_carrier TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS orders_fulfillment ON orders(fulfillment_status);
CREATE TABLE IF NOT EXISTS lookup_limits (
  key TEXT PRIMARY KEY,
  count INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);
