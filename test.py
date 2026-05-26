# migrate_fixed.py
import sqlite3
import psycopg2
from urllib.parse import urlparse
import time

DATABASE_URL = "postgresql://bibel_quiz_user:IBQceDb477BJ0i7DWL4MSIOy6hnkATEO@dpg-d84b0f58nd3s73ctqle0-a.oregon-postgres.render.com/bibel_quiz"

result = urlparse(DATABASE_URL)
PG_CONFIG = {
    "host": result.hostname,
    "database": result.path[1:],
    "user": result.username,
    "password": result.password,
    "port": result.port or 5432,
    "sslmode": "require"
}

def disable_foreign_keys():
    """Disable foreign key checks temporarily"""
    pg_conn = psycopg2.connect(**PG_CONFIG)
    pg_cursor = pg_conn.cursor()
    pg_cursor.execute("SET session_replication_role = 'replica';")
    pg_conn.commit()
    pg_conn.close()
    print("   Foreign key checks disabled")

def enable_foreign_keys():
    """Re-enable foreign key checks"""
    pg_conn = psycopg2.connect(**PG_CONFIG)
    pg_cursor = pg_conn.cursor()
    pg_cursor.execute("SET session_replication_role = 'origin';")
    pg_conn.commit()
    pg_conn.close()
    print("   Foreign key checks re-enabled")

def migrate_table_safe(table_name, columns, skip_columns=None, convert_booleans=None):
    """Migrate table safely with error handling"""
    print(f"📋 Migrating {table_name}...", end=" ", flush=True)
    
    sqlite_conn = sqlite3.connect('db.sqlite3')
    sqlite_cursor = sqlite_conn.cursor()
    
    try:
        pg_conn = psycopg2.connect(**PG_CONFIG)
        pg_cursor = pg_conn.cursor()
        
        # Check if table exists in SQLite
        sqlite_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not sqlite_cursor.fetchone():
            print("(table not found)")
            return 0
        
        # Get column names
        sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
        all_columns = [col[1] for col in sqlite_cursor.fetchall()]
        
        # Filter out columns to skip
        if skip_columns:
            columns_to_use = [col for col in all_columns if col not in skip_columns]
        else:
            columns_to_use = all_columns
        
        # Build SELECT query
        select_cols = ','.join(columns_to_use)
        sqlite_cursor.execute(f"SELECT {select_cols} FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print("(no data)")
            return 0
        
        # Clear existing data
        try:
            pg_cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
        except:
            pass
        
        # Insert data with type conversion
        placeholders = ','.join(['%s'] * len(columns_to_use))
        insert_sql = f"INSERT INTO {table_name} ({','.join(columns_to_use)}) VALUES ({placeholders})"
        
        inserted = 0
        errors = 0
        
        for row in rows:
            try:
                # Convert values
                converted_row = list(row)
                
                # Convert boolean fields
                if convert_booleans:
                    for idx, col_name in enumerate(columns_to_use):
                        if col_name in convert_booleans and converted_row[idx] in (0, 1):
                            converted_row[idx] = bool(converted_row[idx])
                
                pg_cursor.execute(insert_sql, converted_row)
                inserted += 1
            except Exception as e:
                errors += 1
                if errors <= 3:  # Show first 3 errors only
                    print(f"\n   ⚠️  Error on row {inserted + errors}: {str(e)[:100]}")
        
        pg_conn.commit()
        print(f"✅ {inserted}/{len(rows)} rows (errors: {errors})")
        return inserted
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0
    finally:
        sqlite_conn.close()
        pg_conn.close()

def verify_and_fix_foreign_keys():
    """Check and fix missing foreign key references"""
    print("\n🔧 Checking foreign key references...")
    
    pg_conn = psycopg2.connect(**PG_CONFIG)
    pg_cursor = pg_conn.cursor()
    
    # Check for books with invalid testament_id
    pg_cursor.execute("""
        SELECT COUNT(*) FROM books b 
        WHERE testament_id IS NOT NULL 
        AND NOT EXISTS (SELECT 1 FROM testaments t WHERE t.id = b.testament_id)
    """)
    invalid_books = pg_cursor.fetchone()[0]
    if invalid_books > 0:
        print(f"   ⚠️  Found {invalid_books} books with invalid testament_id")
        pg_cursor.execute("""
            UPDATE books SET testament_id = NULL 
            WHERE testament_id IS NOT NULL 
            AND NOT EXISTS (SELECT 1 FROM testaments t WHERE t.id = books.testament_id)
        """)
        pg_conn.commit()
        print(f"   ✅ Fixed {invalid_books} books")
    
    pg_conn.close()

def main():
    print("=" * 60)
    print("🚀 MIGRATING SQLITE TO POSTGRESQL (FIXED VERSION)")
    print("=" * 60)
    
    # Step 1: Disable foreign key checks
    print("\n1️⃣ Disabling foreign key constraints...")
    disable_foreign_keys()
    
    # Step 2: Migrate tables in correct order with proper conversion
    print("\n2️⃣ Migrating tables...")
    
    migrations = [
        # Basic lookup tables
        ('languages', None, ['is_active']),
        ('levels', None, None),
        ('testaments', None, None),
        
        # Main data tables
        ('books', None, None),
        ('chapters', None, None),
        ('verses', None, None),
        
        # Text tables (skip problematic columns)
        ('verse_texts', ['id'], None),  # Skip id column, let PostgreSQL generate
        ('questions', None, None),
        ('question_texts', ['id'], None),
        ('options', None, None),
        ('option_texts', ['id'], None),
        ('explanations', ['id'], None),
    ]
    
    total = 0
    for table, skip_cols, bool_cols in migrations:
        count = migrate_table_safe(table, None, skip_cols, bool_cols)
        total += count
        time.sleep(0.3)
    
    # Step 3: Re-enable foreign key checks
    print("\n3️⃣ Re-enabling foreign key constraints...")
    enable_foreign_keys()
    
    # Step 4: Verify and fix any issues
    verify_and_fix_foreign_keys()
    
    print("\n" + "=" * 60)
    print(f"✅ Migration complete! Processed {total} rows")
    print("=" * 60)

if __name__ == "__main__":
    main()