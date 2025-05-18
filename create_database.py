import sqlite3
import datetime
import random

# Create a new SQLite database
conn = sqlite3.connect('business.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    region TEXT,
    join_date DATE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    price DECIMAL(10, 2),
    stock INTEGER
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    sale_date DATE,
    total_amount DECIMAL(10, 2),
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
    FOREIGN KEY (product_id) REFERENCES products (product_id)
)
''')

# Sample data
customers_data = [
    ('John Doe', 'john@example.com', 'North', '2023-01-15'),
    ('Jane Smith', 'jane@example.com', 'South', '2023-02-20'),
    ('Bob Wilson', 'bob@example.com', 'East', '2023-03-10'),
    ('Alice Brown', 'alice@example.com', 'West', '2023-04-05'),
    ('Charlie Davis', 'charlie@example.com', 'North', '2023-05-12')
]

products_data = [
    ('Laptop Pro', 'Electronics', 1299.99, 50),
    ('Office Chair', 'Furniture', 199.99, 100),
    ('Coffee Maker', 'Appliances', 79.99, 75),
    ('Wireless Mouse', 'Electronics', 29.99, 200),
    ('Desk Lamp', 'Furniture', 39.99, 150),
    ('Keyboard', 'Electronics', 89.99, 120),
    ('Monitor', 'Electronics', 299.99, 80),
    ('Filing Cabinet', 'Furniture', 149.99, 40)
]

# Insert sample data
cursor.executemany('INSERT INTO customers (name, email, region, join_date) VALUES (?, ?, ?, ?)', customers_data)
cursor.executemany('INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)', products_data)

# Generate sample sales data
start_date = datetime.date(2023, 1, 1)
end_date = datetime.date(2024, 3, 31)
days_between = (end_date - start_date).days

sales_data = []
for _ in range(200):  # Generate 200 sales records
    random_days = random.randint(0, days_between)
    sale_date = start_date + datetime.timedelta(days=random_days)
    customer_id = random.randint(1, len(customers_data))
    product_id = random.randint(1, len(products_data))
    quantity = random.randint(1, 5)
    
    # Get product price
    cursor.execute('SELECT price FROM products WHERE product_id = ?', (product_id,))
    price = cursor.fetchone()[0]
    total_amount = price * quantity
    
    sales_data.append((customer_id, product_id, quantity, sale_date, total_amount))

cursor.executemany('INSERT INTO sales (customer_id, product_id, quantity, sale_date, total_amount) VALUES (?, ?, ?, ?, ?)', sales_data)

# Commit changes and close connection
conn.commit()
conn.close()

print("Database created successfully with sample data!") 
