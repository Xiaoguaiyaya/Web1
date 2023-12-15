import pyodbc

# Database connection configuration
db_config = {
    'Driver': '{SQL Server}',
    'Server': 'TESTDUCK\\TABLEMOOEL',
    'Database': 'shxxi',
    'Trusted_Connection': 'no',  # Use SQL Server authentication
    'UID': 'sa',  # Your SQL Server username
    'PWD': '123456'  # Your SQL Server password
}


# Establish a connection
try:
    connection = pyodbc.connect(';'.join([f'{key}={value}' for key, value in db_config.items()]))
    print("Connected successfully!")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'connection' in locals():
        connection.close()
