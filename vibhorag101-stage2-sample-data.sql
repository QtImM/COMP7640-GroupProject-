USE `comp7640_marketplace`;

SET FOREIGN_KEY_CHECKS = 0;

DELETE FROM `vendor_transaction`;
DELETE FROM `order_item`;
DELETE FROM `orders`;
DELETE FROM `product_tag`;
DELETE FROM `product`;
DELETE FROM `customer`;
DELETE FROM `vendor`;

SET FOREIGN_KEY_CHECKS = 1;

INSERT INTO `vendor`
(`vendor_id`, `business_name`, `contact_person`, `email`, `contact_number`, `password_hash`, `geographical_presence`, `average_rating`, `created_at`, `status`)
VALUES
(1, 'Fresh Valley Market', 'Alice Wong', 'alice@freshvalley.com', '852-60000001', 'hash_vendor_1', 'Kowloon', 4.60, NOW(), 'active'),
(2, 'Urban Daily Grocer', 'Brian Chan', 'brian@urbandaily.com', '852-60000002', 'hash_vendor_2', 'Hong Kong Island', 4.30, NOW(), 'active'),
(3, 'Harbour Organic Hub', 'Cindy Lee', 'cindy@harbourorganic.com', '852-60000003', 'hash_vendor_3', 'New Territories', 4.80, NOW(), 'active');

INSERT INTO `customer`
(`customer_id`, `full_name`, `email`, `contact_number`, `shipping_address`, `password_hash`, `created_at`, `status`)
VALUES
(1, 'Tim Zhang', 'tim@example.com', '852-51110001', 'Room 1201, Kowloon Tong', 'hash_customer_1', NOW(), 'active'),
(2, 'Emily Lau', 'emily@example.com', '852-51110002', 'Flat B, Causeway Bay', 'hash_customer_2', NOW(), 'active'),
(3, 'Jason Ho', 'jason@example.com', '852-51110003', 'Block 3, Sha Tin', 'hash_customer_3', NOW(), 'active'),
(4, 'Sophie Ng', 'sophie@example.com', '852-51110004', 'Unit 18, Tseung Kwan O', 'hash_customer_4', NOW(), 'active'),
(5, 'Kevin Yip', 'kevin@example.com', '852-51110005', 'Tower 6, Tsuen Wan', 'hash_customer_5', NOW(), 'active');

INSERT INTO `product`
(`product_id`, `vendor_id`, `product_name`, `listed_price`, `stock_quantity`, `description`, `status`, `created_at`)
VALUES
(1, 1, 'Organic Spinach', 18.00, 100, 'Fresh organic spinach bundle', 'active', NOW()),
(2, 1, 'Cherry Tomato Box', 26.00, 80, 'Sweet cherry tomatoes', 'active', NOW()),
(3, 1, 'Greek Yogurt Cup', 15.50, 120, 'Unsweetened greek yogurt', 'active', NOW()),
(4, 2, 'Whole Wheat Bread', 22.00, 60, 'Bakery fresh whole wheat bread', 'active', NOW()),
(5, 2, 'Low Fat Milk', 28.00, 90, '1L low fat milk', 'active', NOW()),
(6, 2, 'Free Range Eggs', 36.00, 70, 'Pack of 12 eggs', 'active', NOW()),
(7, 3, 'Organic Avocado', 24.00, 50, 'Imported organic avocado', 'active', NOW()),
(8, 3, 'Granola Cereal', 42.00, 40, 'High fiber granola cereal', 'active', NOW()),
(9, 3, 'Almond Milk', 31.00, 65, 'Unsweetened almond milk', 'active', NOW()),
(10, 1, 'Blueberry Pack', 39.00, 55, 'Fresh blueberry box', 'active', NOW()),
(11, 2, 'Chicken Breast Fillet', 58.00, 35, 'Skinless chicken breast', 'active', NOW()),
(12, 3, 'Baby Carrot Pack', 19.00, 75, 'Crunchy baby carrots', 'active', NOW());

INSERT INTO `product_tag`
(`product_id`, `tag_value`)
VALUES
(1, 'vegetable'),
(1, 'organic'),
(1, 'healthy'),
(2, 'vegetable'),
(2, 'fresh'),
(3, 'dairy'),
(3, 'healthy'),
(4, 'bakery'),
(4, 'breakfast'),
(5, 'dairy'),
(5, 'daily'),
(6, 'protein'),
(6, 'breakfast'),
(7, 'organic'),
(7, 'fruit'),
(7, 'healthy'),
(8, 'breakfast'),
(8, 'snack'),
(9, 'dairy-free'),
(9, 'healthy'),
(10, 'fruit'),
(10, 'fresh'),
(11, 'protein'),
(11, 'meat'),
(12, 'vegetable'),
(12, 'snack');

INSERT INTO `orders`
(`order_id`, `customer_id`, `order_date`, `total_price`, `status`, `shipping_address`)
VALUES
(1, 1, NOW(), 91.50, 'placed', 'Room 1201, Kowloon Tong'),
(2, 2, NOW(), 120.00, 'processing', 'Flat B, Causeway Bay'),
(3, 3, NOW(), 97.00, 'shipped', 'Block 3, Sha Tin');

INSERT INTO `order_item`
(`order_item_id`, `order_id`, `product_id`, `vendor_id`, `quantity`, `unit_price`, `subtotal`, `item_status`)
VALUES
(1, 1, 1, 1, 2, 18.00, 36.00, 'placed'),
(2, 1, 4, 2, 1, 22.00, 22.00, 'placed'),
(3, 1, 9, 3, 1, 31.00, 31.00, 'placed'),
(4, 1, 3, 1, 1, 15.50, 15.50, 'placed'),
(5, 2, 7, 3, 2, 24.00, 48.00, 'processing'),
(6, 2, 11, 2, 1, 58.00, 58.00, 'processing'),
(7, 2, 12, 3, 1, 14.00, 14.00, 'processing'),
(8, 3, 6, 2, 1, 36.00, 36.00, 'shipped'),
(9, 3, 10, 1, 1, 39.00, 39.00, 'shipped'),
(10, 3, 12, 3, 1, 22.00, 22.00, 'shipped');

INSERT INTO `vendor_transaction`
(`transaction_id`, `order_id`, `customer_id`, `vendor_id`, `amount`, `payment_method`, `transaction_time`, `transaction_status`)
VALUES
(1, 1, 1, 1, 51.50, 'Credit Card', NOW(), 'paid'),
(2, 1, 1, 2, 22.00, 'Credit Card', NOW(), 'paid'),
(3, 1, 1, 3, 31.00, 'Credit Card', NOW(), 'paid'),
(4, 2, 2, 2, 58.00, 'FPS', NOW(), 'paid'),
(5, 2, 2, 3, 62.00, 'FPS', NOW(), 'paid'),
(6, 3, 3, 1, 39.00, 'Credit Card', NOW(), 'paid'),
(7, 3, 3, 2, 36.00, 'Credit Card', NOW(), 'paid'),
(8, 3, 3, 3, 22.00, 'Credit Card', NOW(), 'paid');

UPDATE `product`
SET `stock_quantity` = CASE `product_id`
  WHEN 1 THEN 98
  WHEN 3 THEN 119
  WHEN 4 THEN 59
  WHEN 6 THEN 69
  WHEN 7 THEN 48
  WHEN 9 THEN 64
  WHEN 10 THEN 54
  WHEN 11 THEN 34
  WHEN 12 THEN 73
  ELSE `stock_quantity`
END
WHERE `product_id` IN (1,3,4,6,7,9,10,11,12);
