# check_tables.py
import psycopg2

try:
    connection = psycopg2.connect(
        host="localhost",
        database="student_data_db",
        user="postgres",
        password="GreninJA95**",  # Use your actual password
        port="5432"
    )
    
    cursor = connection.cursor()
    
    # Get all tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    
    tables = cursor.fetchall()
    
    print("="*60)
    print("TABLES IN DATABASE 'student_data_db':")
    print("="*60)
    for table in tables:
        print(f"- {table[0]}")
    
    # Show sample data from each table
    for table in tables:
        table_name = table[0]
        print(f"\n{'='*60}")
        print(f"Sample data from '{table_name}':")
        print("="*60)
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        rows = cursor.fetchall()
        
        # Get column names
        cursor.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
        """)
        columns = [col[0] for col in cursor.fetchall()]
        print(f"Columns: {columns}")
        
        for row in rows:
            print(row)
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")