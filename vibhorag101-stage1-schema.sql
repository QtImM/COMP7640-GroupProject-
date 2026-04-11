CREATE DATABASE IF NOT EXISTS `comp7640_marketplace`;
USE `comp7640_marketplace`;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `vendor_transaction`;
DROP TABLE IF EXISTS `order_item`;
DROP TABLE IF EXISTS `orders`;
DROP TABLE IF EXISTS `product_tag`;
DROP TABLE IF EXISTS `product`;
DROP TABLE IF EXISTS `customer`;
DROP TABLE IF EXISTS `vendor`;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE `vendor` (
  `vendor_id` BIGINT NOT NULL AUTO_INCREMENT,
  `business_name` VARCHAR(100) NOT NULL,
  `contact_person` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `contact_number` VARCHAR(30) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `geographical_presence` VARCHAR(255) NOT NULL,
  `average_rating` DECIMAL(3,2) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` VARCHAR(20) NOT NULL DEFAULT 'active',
  PRIMARY KEY (`vendor_id`),
  UNIQUE KEY `uq_vendor_email` (`email`),
  KEY `idx_vendor_business_name` (`business_name`),
  KEY `idx_vendor_status` (`status`)
);

CREATE TABLE `customer` (
  `customer_id` BIGINT NOT NULL AUTO_INCREMENT,
  `full_name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `contact_number` VARCHAR(30) NOT NULL,
  `shipping_address` VARCHAR(255) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` VARCHAR(20) NOT NULL DEFAULT 'active',
  PRIMARY KEY (`customer_id`),
  UNIQUE KEY `uq_customer_email` (`email`),
  KEY `idx_customer_status` (`status`)
);

CREATE TABLE `product` (
  `product_id` BIGINT NOT NULL AUTO_INCREMENT,
  `vendor_id` BIGINT NOT NULL,
  `product_name` VARCHAR(150) NOT NULL,
  `listed_price` DECIMAL(10,2) NOT NULL,
  `stock_quantity` INT NOT NULL,
  `description` VARCHAR(500) DEFAULT NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'active',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`product_id`),
  KEY `idx_product_vendor_id` (`vendor_id`),
  KEY `idx_product_name` (`product_name`),
  KEY `idx_product_status` (`status`),
  CONSTRAINT `fk_product_vendor`
    FOREIGN KEY (`vendor_id`) REFERENCES `vendor` (`vendor_id`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT `chk_product_stock_quantity`
    CHECK (`stock_quantity` >= 0),
  CONSTRAINT `chk_product_listed_price`
    CHECK (`listed_price` >= 0)
);

CREATE TABLE `product_tag` (
  `product_tag_id` BIGINT NOT NULL AUTO_INCREMENT,
  `product_id` BIGINT NOT NULL,
  `tag_value` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`product_tag_id`),
  UNIQUE KEY `uq_product_tag_value` (`product_id`, `tag_value`),
  KEY `idx_product_tag_value` (`tag_value`),
  CONSTRAINT `fk_product_tag_product`
    FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

CREATE TABLE `orders` (
  `order_id` BIGINT NOT NULL AUTO_INCREMENT,
  `customer_id` BIGINT NOT NULL,
  `order_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `total_price` DECIMAL(10,2) NOT NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'placed',
  `shipping_address` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`order_id`),
  KEY `idx_orders_customer_id` (`customer_id`),
  KEY `idx_orders_status` (`status`),
  KEY `idx_orders_order_date` (`order_date`),
  CONSTRAINT `fk_orders_customer`
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT `chk_orders_total_price`
    CHECK (`total_price` >= 0)
);

CREATE TABLE `order_item` (
  `order_item_id` BIGINT NOT NULL AUTO_INCREMENT,
  `order_id` BIGINT NOT NULL,
  `product_id` BIGINT NOT NULL,
  `vendor_id` BIGINT NOT NULL,
  `quantity` INT NOT NULL,
  `unit_price` DECIMAL(10,2) NOT NULL,
  `subtotal` DECIMAL(10,2) NOT NULL,
  `item_status` VARCHAR(20) NOT NULL DEFAULT 'placed',
  PRIMARY KEY (`order_item_id`),
  KEY `idx_order_item_order_id` (`order_id`),
  KEY `idx_order_item_product_id` (`product_id`),
  KEY `idx_order_item_vendor_id` (`vendor_id`),
  CONSTRAINT `fk_order_item_order`
    FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT `fk_order_item_product`
    FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT `fk_order_item_vendor`
    FOREIGN KEY (`vendor_id`) REFERENCES `vendor` (`vendor_id`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT `chk_order_item_quantity`
    CHECK (`quantity` > 0),
  CONSTRAINT `chk_order_item_unit_price`
    CHECK (`unit_price` >= 0),
  CONSTRAINT `chk_order_item_subtotal`
    CHECK (`subtotal` >= 0)
);

CREATE TABLE `vendor_transaction` (
  `transaction_id` BIGINT NOT NULL AUTO_INCREMENT,
  `order_id` BIGINT NOT NULL,
  `customer_id` BIGINT NOT NULL,
  `vendor_id` BIGINT NOT NULL,
  `amount` DECIMAL(10,2) NOT NULL,
  `payment_method` VARCHAR(30) NOT NULL,
  `transaction_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `transaction_status` VARCHAR(20) NOT NULL DEFAULT 'paid',
  PRIMARY KEY (`transaction_id`),
  KEY `idx_vendor_transaction_order_id` (`order_id`),
  KEY `idx_vendor_transaction_customer_id` (`customer_id`),
  KEY `idx_vendor_transaction_vendor_id` (`vendor_id`),
  KEY `idx_vendor_transaction_status` (`transaction_status`),
  CONSTRAINT `fk_vendor_transaction_order`
    FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT `fk_vendor_transaction_customer`
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT `fk_vendor_transaction_vendor`
    FOREIGN KEY (`vendor_id`) REFERENCES `vendor` (`vendor_id`)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT `chk_vendor_transaction_amount`
    CHECK (`amount` >= 0)
);

-- Notes:
-- 1. Product tags are modeled in a separate table for flexible search.
-- 2. "At most 3 tags per product" should be enforced in application logic
--    or via a trigger added in a later phase.
-- 3. A single order can span multiple vendors through multiple rows in
--    `order_item`, and each vendor-level payment is captured in
--    `vendor_transaction`.
