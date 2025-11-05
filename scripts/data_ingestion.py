# data_ingestion.py
"""
Data Ingestion Module
Handles loading data from various sources: CSV, Excel, Database, API
"""

import os
import pandas as pd
import requests
from sqlalchemy import create_engine

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data")

class DataIngestion:
    """Handles data loading from multiple sources"""
    
    def __init__(self, db_url=None):
        """
        Initialize DataIngestion
        
        Args:
            db_url: Database connection URL (optional)
        """
        self.engine = create_engine(db_url) if db_url else None
        
        # Create data directory if it doesn't exist
        os.makedirs(DATA_DIR, exist_ok=True)

    def load_csv(self, file_name):
        """
        Load data from CSV file
        
        Args:
            file_name: Name of CSV file or full path
            
        Returns:
            pandas.DataFrame or None
        """
        # Check if it's a full path or just filename
        if os.path.isabs(file_name):
            file_path = file_name
        else:
            file_path = os.path.join(DATA_DIR, file_name)
        
        try:
            df = pd.read_csv(file_path)
            print(f"✓ CSV loaded successfully: {file_path}")
            print(f"  Shape: {df.shape}")
            return df
        except FileNotFoundError:
            print(f"❌ Error: File not found - {file_path}")
            return None
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return None

    def load_excel(self, file_name, sheet_name=0):
        """
        Load data from Excel file
        
        Args:
            file_name: Name of Excel file or full path
            sheet_name: Sheet name or index (default: 0)
            
        Returns:
            pandas.DataFrame or None
        """
        # Check if it's a full path or just filename
        if os.path.isabs(file_name):
            file_path = file_name
        else:
            file_path = os.path.join(DATA_DIR, file_name)
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"✓ Excel loaded successfully: {file_path}")
            print(f"  Sheet: {sheet_name}")
            print(f"  Shape: {df.shape}")
            return df
        except FileNotFoundError:
            print(f"❌ Error: File not found - {file_path}")
            return None
        except Exception as e:
            print(f"❌ Error loading Excel: {e}")
            return None

    def load_from_database(self, query):
        """
        Load data from database using SQL query
        
        Args:
            query: SQL query string
            
        Returns:
            pandas.DataFrame or None
        """
        if not self.engine:
            print("❌ Error: Database engine not configured")
            return None
        
        try:
            df = pd.read_sql(query, self.engine)
            print(f"✓ Data loaded successfully from database")
            print(f"  Rows: {len(df)}")
            return df
        except Exception as e:
            print(f"❌ Error loading from database: {e}")
            return None

    def fetch_from_api(self, url, params=None):
        """
        Load data from API endpoint
        
        Args:
            url: API endpoint URL
            params: Optional query parameters
            
        Returns:
            pandas.DataFrame or None
        """
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Try to find the data array in the response
                for key in ['data', 'results', 'items']:
                    if key in data and isinstance(data[key], list):
                        df = pd.DataFrame(data[key])
                        break
                else:
                    df = pd.DataFrame([data])
            else:
                print(f"❌ Error: Unexpected API response format")
                return None
            
            print(f"✓ Data loaded successfully from API: {url}")
            print(f"  Rows: {len(df)}")
            return df
        except requests.exceptions.RequestException as e:
            print(f"❌ Error loading from API: {e}")
            return None
        except Exception as e:
            print(f"❌ Error processing API response: {e}")
            return None

    def save_to_database(self, df, table_name, if_exists='replace'):
        """
        Save DataFrame to database
        
        Args:
            df: pandas.DataFrame to save
            table_name: Name of database table
            if_exists: How to behave if table exists ('fail', 'replace', 'append')
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.engine:
            print("❌ Error: Database engine not configured")
            return False
        
        try:
            df.to_sql(table_name, self.engine, if_exists=if_exists, index=False)
            print(f"✓ Data saved successfully to table: {table_name}")
            print(f"  Rows saved: {len(df)}")
            return True
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            return False

    def connect_to_database(self, db_url):
        """
        Establish or update database connection
        
        Args:
            db_url: Database connection URL
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.engine = create_engine(db_url)
            # Test connection
            with self.engine.connect() as connection:
                print(f"✓ Database connection established successfully")
            return True
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
            return False