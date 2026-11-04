-- Keep legacy CJ columns for existing CSV integrations; new neutral columns carry the correct supplier.
ALTER TABLE orders ADD COLUMN supplier_id TEXT NOT NULL DEFAULT 'cj';
ALTER TABLE orders ADD COLUMN supplier_sku TEXT;
ALTER TABLE orders ADD COLUMN supplier_variant_id TEXT;
UPDATE orders SET supplier_sku=cj_sku,supplier_variant_id=cj_variant_id WHERE supplier_id='cj' AND supplier_sku IS NULL;
CREATE INDEX IF NOT EXISTS orders_by_supplier ON orders(supplier_id,fulfillment_status);
