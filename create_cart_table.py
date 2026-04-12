
import pymysql
import yaml

def execute_sql(sql_command):
    try:
        with open('database.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        conn = pymysql.connect(
            host=config.get('mysql_host', '127.0.0.1'),
            user=config.get('mysql_user', 'root'),
            password=config.get('mysql_password', ''),
            database=config.get('mysql_db', 'comp7640_marketplace'),
            charset='utf8mb4'
        )
        cur = conn.cursor()
        cur.execute(sql_command)
        conn.commit()
        cur.close()
        conn.close()
        print("SQL executed successfully.")
    except Exception as e:
        print(f"Error executing SQL: {e}")

if __name__ == "__main__":
    sql = """
    CREATE TABLE IF NOT EXISTS `cart_item` (
      `cart_item_id` BIGINT NOT NULL AUTO_INCREMENT,
      `customer_id` BIGINT NOT NULL,
      `product_id` BIGINT NOT NULL,
      `quantity` INT NOT NULL DEFAULT 1,
      `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (`cart_item_id`),
      CONSTRAINT `fk_cart_item_customer` FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`) ON DELETE CASCADE,
      CONSTRAINT `fk_cart_item_product` FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`) ON DELETE CASCADE
    );
    """
    execute_sql(sql)
