ALTER TABLE checkout_intents ADD COLUMN delivery_phone TEXT;

CREATE TABLE launch_order_claim (
  offer_id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL REFERENCES checkout_intents(order_id)
);
