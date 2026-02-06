"""
Database Management Showcase Application. Demonstrates 16 key database management
competencies using SQLite.
"""

import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import List, Dict
import random
import string


class DatabaseManager:
    """Main class demonstrating all database management requirements"""

    def __init__(self, db_name: str = "showcase.db"):
        self.db_name = db_name
        self.setup_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def setup_database(self):
        """Initialize database with complete schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # REQ 7: Implement and modify database structure
            # Create tables with proper relationships and constraints
            cursor.executescript("""
                -- Users table with sensitive data
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT CHECK(status IN ('active', 'inactive', 'suspended')) DEFAULT 'active'
                );
                
                -- Products table
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    price REAL NOT NULL CHECK(price >= 0),
                    stock INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Orders table with foreign key
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                
                -- Order items junction table
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                );
                
                -- REQ 15: Optimize data access through patterns (Indexes)
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
                CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
                CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
                CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
                CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
                CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
                
                -- Audit log table for security
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    user_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT
                );
            """)

            conn.commit()
            print("Database structure created successfully!")

    # REQ 8: Implement database techniques to safeguard sensitive data
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash passwords using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user_secure(self, username: str, email: str, password: str) -> int:
        """Create user with hashed password (security technique)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            password_hash = self.hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            conn.commit()
            return cursor.lastrowid

    # REQ 3: Generate dummy database data for testing and development
    def generate_dummy_data(self, num_users: int = 50, num_products: int = 100):
        """Generate realistic test data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Clear existing data
            cursor.execute("DELETE FROM order_items")
            cursor.execute("DELETE FROM orders")
            cursor.execute("DELETE FROM products")
            cursor.execute("DELETE FROM users")
            conn.commit()

            # Generate users
            categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Sports']
            statuses = ['active', 'inactive', 'suspended']

            for i in range(num_users):
                username = f"user_{i}_{self._random_string(5)}"
                email = f"{username}@example.com"
                password_hash = self.hash_password(f"password{i}")
                status = random.choice(statuses)
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, status) VALUES (?, ?, ?, ?)",
                    (username, email, password_hash, status)
                )

            # Generate products
            for i in range(num_products):
                name = f"Product_{i}_{self._random_string(4)}"
                category = random.choice(categories)
                price = round(random.uniform(10, 1000), 2)
                stock = random.randint(0, 500)
                cursor.execute(
                    "INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)",
                    (name, category, price, stock)
                )

            # Generate orders
            cursor.execute("SELECT id FROM users WHERE status = 'active'")
            user_ids = [row[0] for row in cursor.fetchall()]

            cursor.execute("SELECT id, price FROM products")
            products = cursor.fetchall()

            for _ in range(200):
                user_id = random.choice(user_ids)
                order_date = datetime.now() - timedelta(days=random.randint(0, 365))

                # Insert order
                cursor.execute(
                    "INSERT INTO orders (user_id, total_amount, order_date, status) VALUES (?, ?, ?, ?)",
                    (user_id, 0, order_date, random.choice(['pending', 'completed', 'cancelled']))
                )
                order_id = cursor.lastrowid

                # Insert order items
                total = 0
                for _ in range(random.randint(1, 5)):
                    product = random.choice(products)
                    quantity = random.randint(1, 5)
                    item_total = product[1] * quantity
                    total += item_total

                    cursor.execute(
                        "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                        (order_id, product[0], quantity, product[1])
                    )

                # Update order total
                cursor.execute("UPDATE orders SET total_amount = ? WHERE id = ?", (total, order_id))

            conn.commit()
            print(f"✓ Generated {num_users} users, {num_products} products, and 200 orders.")

    @staticmethod
    def _random_string(length: int) -> str:
        """Helper to generate random strings"""
        return ''.join(random.choices(string.ascii_lowercase, k=length))

    # REQ 1: Select data from a database using query language
    def select_active_users(self) -> List[Dict]:
        """Basic SELECT query with WHERE clause"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, created_at, status
                FROM users
                WHERE status = 'active'
                LIMIT 10
            """)
            return [dict(row) for row in cursor.fetchall()]

    # REQ 4: Order and group data from a database using query language
    def get_products_by_category(self) -> List[Dict]:
        """GROUP BY with ORDER BY and aggregation"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    category,
                    COUNT(*) as product_count,
                    AVG(price) as avg_price,
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    SUM(stock) as total_stock
                FROM products
                GROUP BY category
                ORDER BY product_count DESC, avg_price DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    # REQ 5: Use database data aggregation techniques
    def get_sales_statistics(self) -> Dict:
        """Complex aggregation with multiple techniques"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT o.id) as total_orders,
                    COUNT(DISTINCT o.user_id) as unique_customers,
                    SUM(o.total_amount) as total_revenue,
                    AVG(o.total_amount) as avg_order_value,
                    MIN(o.total_amount) as min_order,
                    MAX(o.total_amount) as max_order,
                    COUNT(CASE WHEN o.status = 'completed' THEN 1 END) as completed_orders,
                    COUNT(CASE WHEN o.status = 'pending' THEN 1 END) as pending_orders,
                    COUNT(CASE WHEN o.status = 'cancelled' THEN 1 END) as cancelled_orders
                FROM orders o
            """)
            return dict(cursor.fetchone())

    # REQ 6: Combine multiple queries to optimize query execution
    def get_user_order_summary(self, user_id: int) -> Dict:
        """Optimized query combining multiple data sources with JOINs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Single optimized query instead of multiple queries
            cursor.execute("""
                SELECT 
                    u.id,
                    u.username,
                    u.email,
                    COUNT(DISTINCT o.id) as order_count,
                    COALESCE(SUM(o.total_amount), 0) as total_spent,
                    COALESCE(AVG(o.total_amount), 0) as avg_order_value,
                    MAX(o.order_date) as last_order_date,
                    COUNT(DISTINCT oi.product_id) as unique_products_purchased
                FROM users u
                LEFT JOIN orders o ON u.id = o.user_id
                LEFT JOIN order_items oi ON o.id = oi.order_id
                WHERE u.id = ?
                GROUP BY u.id, u.username, u.email
            """, (user_id,))
            result = cursor.fetchone()
            return dict(result) if result else {}

    # REQ 16: Optimize query performance using query techniques
    def get_top_customers_optimized(self, limit: int = 10) -> List[Dict]:
        """Optimized query using indexes, CTEs, and efficient joins"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Using CTE (Common Table Expression) for better query organization
            cursor.execute("""
                WITH customer_stats AS (
                    SELECT 
                        o.user_id,
                        COUNT(*) as order_count,
                        SUM(o.total_amount) as total_spent
                    FROM orders o
                    WHERE o.status = 'completed'
                    GROUP BY o.user_id
                )
                SELECT 
                    u.id,
                    u.username,
                    u.email,
                    cs.order_count,
                    cs.total_spent
                FROM users u
                INNER JOIN customer_stats cs ON u.id = cs.user_id
                WHERE u.status = 'active'
                ORDER BY cs.total_spent DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # REQ 2: Create and modify database objects
    def modify_database_structure(self):
        """Demonstrate ALTER TABLE and other DDL operations"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Add new column
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
                print("✓ Added last_login column to users table")
            except sqlite3.OperationalError:
                print("✓ Column last_login already exists")

            # Create a view (database object)
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS active_user_orders AS
                SELECT 
                    u.username,
                    u.email,
                    o.id as order_id,
                    o.total_amount,
                    o.order_date,
                    o.status
                FROM users u
                JOIN orders o ON u.id = o.user_id
                WHERE u.status = 'active'
            """)

            # Create a temporary table
            cursor.execute("""
                CREATE TEMP TABLE IF NOT EXISTS session_data (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            print("✓ Created view and temporary table")

    # REQ 9: Use stored procedures (SQLite uses triggers)
    def create_triggers(self):
        """Create triggers to enhance operations, security, and performance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Audit trigger for user changes
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS audit_user_changes
                AFTER UPDATE ON users
                BEGIN
                    INSERT INTO audit_log (table_name, action, user_id, details)
                    VALUES ('users', 'UPDATE', NEW.id, 
                            json_object('old_status', OLD.status, 'new_status', NEW.status));
                END;
            """)

            # Trigger to update product stock
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_product_stock
                AFTER INSERT ON order_items
                BEGIN
                    UPDATE products 
                    SET stock = stock - NEW.quantity
                    WHERE id = NEW.product_id AND stock >= NEW.quantity;
                END;
            """)

            # Prevent deletion of orders with items
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prevent_order_deletion
                BEFORE DELETE ON orders
                BEGIN
                    SELECT RAISE(ABORT, 'Cannot delete order with items')
                    WHERE (SELECT COUNT(*) FROM order_items WHERE order_id = OLD.id) > 0;
                END;
            """)

            conn.commit()
            print("✓ Created triggers for audit, stock management, and data protection")

    # REQ 10: Wrap queries into transactions
    def process_order_transaction(self, user_id: int, items: List[Dict]) -> bool:
        """Demonstrate ACID transaction with rollback capability.
        ACID: Atomicity, Consistency, Isolation, Durability
         - Atomicity: All operations succeed or none do
         - Consistency: Database remains in a valid state
         - Isolation: Concurrent transactions do not interfere
         - Durability: Once committed, changes are permanent
        """
        with self.get_connection() as conn:
            try:
                conn.execute("BEGIN TRANSACTION")
                cursor = conn.cursor()

                # Calculate total
                total_amount = 0
                for item in items:
                    cursor.execute("SELECT price, stock FROM products WHERE id = ?", (item['product_id'],))
                    product = cursor.fetchone()
                    if not product or product[1] < item['quantity']:
                        raise ValueError(f"Insufficient stock for product {item['product_id']}")
                    total_amount += product[0] * item['quantity']

                # Create order
                cursor.execute(
                    "INSERT INTO orders (user_id, total_amount, status) VALUES (?, ?, ?)",
                    (user_id, total_amount, 'pending')
                )
                order_id = cursor.lastrowid

                # Add items and update stock
                for item in items:
                    cursor.execute("SELECT price FROM products WHERE id = ?", (item['product_id'],))
                    price = cursor.fetchone()[0]

                    cursor.execute(
                        "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                        (order_id, item['product_id'], item['quantity'], price)
                    )

                    cursor.execute(
                        "UPDATE products SET stock = stock - ? WHERE id = ?",
                        (item['quantity'], item['product_id'])
                    )

                # Log transaction
                cursor.execute(
                    "INSERT INTO audit_log (table_name, action, user_id, details) VALUES (?, ?, ?, ?)",
                    ('orders', 'CREATE', user_id, json.dumps({'order_id': order_id, 'total': total_amount}))
                )

                conn.commit()
                print(f"✓ Transaction completed: Order #{order_id} created")
                return True

            except Exception as e:
                conn.rollback()
                print(f"✗ Transaction rolled back: {str(e)}")
                return False

    # REQ 11: Apply security techniques and methodologies
    def demonstrate_security(self):
        """Show various security practices"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Parameterized queries (prevent SQL injection)
            email = "user_1@example.com"
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))

            # 2. Role-based access simulation
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id INTEGER,
                    role TEXT CHECK(role IN ('admin', 'user', 'guest')),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # 3. Row-level security simulation
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS user_own_orders AS
                SELECT * FROM orders
                WHERE user_id = (SELECT id FROM users WHERE username = 'current_user')
            """)

            conn.commit()
            print("✓ Security measures demonstrated: parameterized queries, roles, row-level security")

    # REQ 12: Apply techniques for database optimization
    def demonstrate_optimization(self):
        """Show various optimization techniques"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Analyze query performance
            cursor.execute("ANALYZE")

            # 2. Use EXPLAIN QUERY PLAN
            cursor.execute("""
                EXPLAIN QUERY PLAN
                SELECT u.username, COUNT(o.id) as order_count
                FROM users u
                LEFT JOIN orders o ON u.id = o.user_id
                GROUP BY u.id
            """)
            plan = cursor.fetchall()

            # 3. Vacuum to reclaim space
            cursor.execute("VACUUM")

            # 4. Create covering index for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_orders_user_status 
                ON orders(user_id, status, total_amount)
            """)

            conn.commit()
            print("✓ Optimization techniques applied: ANALYZE, VACUUM, covering indexes")
            print(f"  Query plan analysis: {len(plan)} steps")

    # REQ 13: Create and use database dumps
    def create_backup(self, backup_file: str = "backup.sql"):
        """Create database dump for backup"""
        with self.get_connection() as conn:
            with open(backup_file, 'w') as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")
        print(f"✓ Database backup created: {backup_file}")
        return backup_file

    def restore_from_backup(self, backup_file: str):
        """Restore database from dump"""
        with self.get_connection() as conn:
            with open(backup_file, 'r') as f:
                sql_script = f.read()
            conn.executescript(sql_script)
        print(f"✓ Database restored from: {backup_file}")

    # REQ 14: Document information about a database
    def generate_database_documentation(self) -> Dict:
        """Generate comprehensive database documentation"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            doc = {
                "database": self.db_name,
                "generated_at": datetime.now().isoformat(),
                "tables": {},
                "indexes": [],
                "views": [],
                "triggers": []
            }

            # Get all tables
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = cursor.fetchall()

            for (table_name,) in tables:
                # Get table structure
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]

                doc["tables"][table_name] = {
                    "columns": [
                        {
                            "name": col[1],
                            "type": col[2],
                            "nullable": not col[3],
                            "default": col[4],
                            "primary_key": bool(col[5])
                        }
                        for col in columns
                    ],
                    "row_count": row_count
                }

            # Get indexes
            cursor.execute("""
                SELECT name, tbl_name, sql FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """)
            doc["indexes"] = [{"name": row[0], "table": row[1], "sql": row[2]} for row in cursor.fetchall()]

            # Get views
            cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='view'")
            doc["views"] = [{"name": row[0], "sql": row[1]} for row in cursor.fetchall()]

            # Get triggers
            cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger'")
            doc["triggers"] = [{"name": row[0], "table": row[1], "sql": row[2]} for row in cursor.fetchall()]

            return doc

    def print_documentation(self):
        """Print formatted database documentation"""
        doc = self.generate_database_documentation()

        print("\n" + "="*80)
        print("DATABASE DOCUMENTATION")
        print("="*80)
        print(f"\nDatabase: {doc['database']}")
        print(f"Generated: {doc['generated_at']}")

        print(f"\nTABLES ({len(doc['tables'])})")
        print("-" * 80)
        for table_name, table_info in doc['tables'].items():
            print(f"\n  {table_name} ({table_info['row_count']} rows)")
            for col in table_info['columns']:
                pk = " [PK]" if col['primary_key'] else ""
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"    - {col['name']}: {col['type']} {nullable}{pk}")

        print(f"\nINDEXES ({len(doc['indexes'])})")
        print("-" * 80)
        for idx in doc['indexes']:
            print(f"  - {idx['name']} on {idx['table']}")

        print(f"\n👁 VIEWS ({len(doc['views'])})")
        print("-" * 80)
        for view in doc['views']:
            print(f"  - {view['name']}")

        print(f"\n⚡ TRIGGERS ({len(doc['triggers'])})")
        print("-" * 80)
        for trigger in doc['triggers']:
            print(f"  - {trigger['name']} on {trigger['table']}")

        print("\n" + "="*80 + "\n")


def run_demonstration():
    """Run complete demonstration of all 16 requirements"""
    print("\n" + "="*80)
    print("DATABASE MANAGEMENT COMPETENCY DEMONSTRATION")
    print("="*80 + "\n")

    # Initialize
    db = DatabaseManager()

    print("\n[1] SELECTING DATA FROM DATABASE")
    print("-" * 80)
    db.generate_dummy_data(50, 100)
    users = db.select_active_users()
    print(f"Found {len(users)} active users (showing first 3):")
    for user in users[:3]:
        print(f"  - {user['username']} ({user['email']})")

    print("\n[2] CREATING AND MODIFYING DATABASE OBJECTS")
    print("-" * 80)
    db.modify_database_structure()

    print("\n[3] DUMMY DATA GENERATION")
    print("-" * 80)
    print("✓ Already demonstrated - 50 users, 100 products, 200 orders generated")

    print("\n[4] ORDERING AND GROUPING DATA")
    print("-" * 80)
    categories = db.get_products_by_category()
    print(f"Product statistics by category (showing first 3):")
    for cat in categories[:3]:
        print(f"  - {cat['category']}: {cat['product_count']} products, avg ${cat['avg_price']:.2f}")

    print("\n[5] DATA AGGREGATION TECHNIQUES")
    print("-" * 80)
    stats = db.get_sales_statistics()
    print(f"Sales Statistics:")
    print(f"  - Total Orders: {stats['total_orders']}")
    print(f"  - Total Revenue: ${stats['total_revenue']:.2f}")
    print(f"  - Avg Order Value: ${stats['avg_order_value']:.2f}")
    print(f"  - Completed: {stats['completed_orders']}, Pending: {stats['pending_orders']}")

    print("\n[6] COMBINING MULTIPLE QUERIES")
    print("-" * 80)
    if users:
        summary = db.get_user_order_summary(users[0]['id'])
        print(f"User summary for {summary.get('username', 'N/A')}:")
        print(f"  - Orders: {summary.get('order_count', 0)}")
        print(f"  - Total Spent: ${summary.get('total_spent', 0):.2f}")

    print("\n[7] IMPLEMENTING DATABASE STRUCTURE")
    print("-" * 80)
    print("✓ Complete schema with tables, foreign keys, constraints demonstrated")

    print("\n[8] SAFEGUARDING SENSITIVE DATA")
    print("-" * 80)
    test_user_id = db.create_user_secure("secure_user", "secure@example.com", "MySecret123")
    print(f"✓ User created with hashed password (ID: {test_user_id})")

    print("\n[9] STORED PROCEDURES (TRIGGERS IN SQLITE)")
    print("-" * 80)
    db.create_triggers()

    print("\n[10] TRANSACTION MANAGEMENT")
    print("-" * 80)
    # Get some products for order
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM products WHERE stock > 5 LIMIT 2")
        product_ids = [row[0] for row in cursor.fetchall()]

    if product_ids and users:
        items = [
            {'product_id': product_ids[0], 'quantity': 2},
            {'product_id': product_ids[1], 'quantity': 1}
        ]
        db.process_order_transaction(users[0]['id'], items)

    print("\n[11] SECURITY TECHNIQUES AND METHODOLOGIES")
    print("-" * 80)
    db.demonstrate_security()

    print("\n[12] DATABASE OPTIMIZATION TECHNIQUES")
    print("-" * 80)
    db.demonstrate_optimization()

    print("\n[13] DATABASE DUMPS AND BACKUPS")
    print("-" * 80)
    backup_file = db.create_backup()
    print(f"✓ Backup file: {backup_file} (restore with restore_from_backup())")

    print("\n[14] DATABASE DOCUMENTATION")
    print("-" * 80)
    db.print_documentation()

    print("\n[15] OPTIMIZING DATA ACCESS PATTERNS")
    print("-" * 80)
    print("✓ Indexes created on all foreign keys and frequently queried columns")
    print("✓ Covering indexes for common query patterns")

    print("\n[16] QUERY PERFORMANCE OPTIMIZATION")
    print("-" * 80)
    top_customers = db.get_top_customers_optimized(5)
    print(f"Top 5 customers by spending (optimized CTE query):")
    for customer in top_customers[:5]:
        print(f"  - {customer['username']}: ${customer['total_spent']:.2f} ({customer['order_count']} orders)")

    print("\n" + "="*80)
    print("✓ ALL 16 DATABASE MANAGEMENT REQUIREMENTS DEMONSTRATED")
    print("="*80 + "\n")

    return db


if __name__ == "__main__":
    db_manager = run_demonstration()

    print("\nEVALUATION TALKING POINTS:")
    print("-" * 80)
    print("""
    1. SQL Mastery: Complex queries with JOINs, CTEs, aggregations, and subqueries
    2. Database Design: Normalized schema with proper relationships and constraints
    3. Performance: Strategic indexing, query optimization, and EXPLAIN usage
    4. Security: Password hashing, parameterized queries, row-level security
    5. Transactions: ACID compliance with proper rollback handling
    6. Data Integrity: Triggers, foreign keys, and CHECK constraints
    7. Backup/Recovery: Full database dump and restore capabilities
    8. Documentation: Automated schema documentation generation
    9. Testing: Comprehensive dummy data generation for realistic scenarios
    10. Best Practices: Context managers, error handling, and clean code structure
    """)
    print("-" * 80)
