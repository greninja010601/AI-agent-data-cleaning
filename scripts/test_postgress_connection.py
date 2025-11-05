import psycopg2
from psycopg2 import Error

try:
    # Connect to PostgreSQL database
    connection = psycopg2.connect(
        host="localhost",        # or your server IP/hostname
        database="student_data_db",
        user="postgres",
        password="GreninJA95**",
        port="5432"             # default PostgreSQL port
    )
    
    # Create a cursor object
    cursor = connection.cursor()
    
    # Print PostgreSQL connection properties
    print("PostgreSQL connection is successful")
    print(connection.get_dsn_parameters(), "\n")
    
    # Execute a test query
    cursor.execute("SELECT version();")
    record = cursor.fetchone()
    print("You are connected to:", record, "\n")
    
    # Example: Execute a simple query
    cursor.execute("SELECT * FROM student_data LIMIT 5;")
    rows = cursor.fetchall()
    
    for row in rows:
        print(row)

except (Exception, Error) as error:
    print("Error while connecting to PostgreSQL:", error)

finally:
    # Close cursor and connection
    if connection:
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")