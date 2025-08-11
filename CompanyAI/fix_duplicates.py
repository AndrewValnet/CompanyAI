import psycopg2

# Database connection parameters
DB_PARAMS = {
    'host': 'localhost',
    'database': 'CompanyAI',
    'user': 'postgres',
    'password': 'password',
    'port': 5432
}

def fix_duplicates():
    """Remove duplicate companies from reached_out_companies table"""
    
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        print("Connected to database successfully!")
        
        # First, let's see the current state
        cursor.execute("SELECT COUNT(*) FROM reached_out_companies")
        before_count = cursor.fetchone()[0]
        print(f"Before cleanup: {before_count} rows")
        
        # Find duplicates
        cursor.execute("""
            SELECT website, COUNT(*) as count 
            FROM reached_out_companies 
            WHERE website IS NOT NULL 
            GROUP BY website 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)
        duplicates = cursor.fetchall()
        
        print(f"\nFound {len(duplicates)} websites with duplicates:")
        for website, count in duplicates[:10]:
            print(f"  {website}: {count} times")
        
        # Remove duplicates using a CTE to keep the first occurrence
        print("\nRemoving duplicates...")
        
        # Method 1: Delete duplicates keeping the lowest ID for each website
        cursor.execute("""
            DELETE FROM reached_out_companies 
            WHERE id NOT IN (
                SELECT MIN(id) 
                FROM reached_out_companies 
                WHERE website IS NOT NULL AND website != ''
                GROUP BY website
            )
            AND website IS NOT NULL 
            AND website != ''
        """)
        
        deleted_count = cursor.fetchone()[0] if cursor.rowcount == -1 else cursor.rowcount
        print(f"Deleted {deleted_count} duplicate rows")
        
        # Also remove rows with empty websites
        cursor.execute("DELETE FROM reached_out_companies WHERE website IS NULL OR website = ''")
        empty_deleted = cursor.fetchone()[0] if cursor.rowcount == -1 else cursor.rowcount
        print(f"Deleted {empty_deleted} rows with empty websites")
        
        # Check final count
        cursor.execute("SELECT COUNT(*) FROM reached_out_companies")
        after_count = cursor.fetchone()[0]
        print(f"\nAfter cleanup: {after_count} rows")
        print(f"Total rows removed: {before_count - after_count}")
        
        # Verify no more duplicates
        cursor.execute("""
            SELECT website, COUNT(*) as count 
            FROM reached_out_companies 
            WHERE website IS NOT NULL 
            GROUP BY website 
            HAVING COUNT(*) > 1
        """)
        remaining_duplicates = cursor.fetchall()
        
        if not remaining_duplicates:
            print("✅ No more duplicates found!")
        else:
            print(f"⚠️  Still have {len(remaining_duplicates)} duplicates")
        
        # Show sample of cleaned data
        print("\n=== SAMPLE OF CLEANED DATA ===")
        cursor.execute("""
            SELECT id, name, website, vertical, subvertical, description, location, monthly_visits, us_percentage
            FROM reached_out_companies 
            ORDER BY id 
            LIMIT 5
        """)
        sample_rows = cursor.fetchall()
        
        for row in sample_rows:
            print(f"ID: {row[0]}, Name: {row[1]}, Website: {row[2]}, Vertical: {row[3]}, Subvertical: {row[4]}, Description: {row[5]}, Location: {row[6]}, Monthly Visits: {row[7]}, US %: {row[8]}")
        
        # Commit the changes
        conn.commit()
        print("\n✅ Database cleanup completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_duplicates()
