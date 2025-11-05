# data_cleaning.py
"""
Data Cleaning Module
Traditional rule-based data cleaning operations
"""

import pandas as pd
import numpy as np

class DataCleaning:
    """Traditional rule-based data cleaning"""
    
    def __init__(self, df):
        """
        Initialize DataCleaning
        
        Args:
            df: pandas.DataFrame to clean
        """
        self.df = df.copy()
        self.original_shape = df.shape
        self.cleaning_log = []
    
    def log_action(self, action):
        """Log cleaning actions"""
        self.cleaning_log.append(action)
        print(f"✓ {action}")
    
    def remove_duplicates(self, subset=None, keep='first'):
        """
        Remove duplicate rows
        
        Args:
            subset: Column labels to consider for identifying duplicates
            keep: Which duplicates to keep ('first', 'last', False)
            
        Returns:
            self (for method chaining)
        """
        initial_rows = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset, keep=keep)
        removed = initial_rows - len(self.df)
        self.log_action(f"Removed {removed} duplicate rows")
        return self
    
    def handle_missing_values(self, strategy='drop', columns=None, fill_value=None):
        """
        Handle missing values
        
        Args:
            strategy: 'drop', 'fill_mean', 'fill_median', 'fill_mode', 'fill_forward', 'fill_backward', 'fill_value'
            columns: List of columns to apply strategy to (None = all columns)
            fill_value: Value to use when strategy='fill_value'
            
        Returns:
            self (for method chaining)
        """
        missing_before = self.df.isnull().sum().sum()
        
        if columns is None:
            columns = self.df.columns
        
        if strategy == 'drop':
            self.df = self.df.dropna(subset=columns)
        elif strategy == 'fill_mean':
            for col in columns:
                if self.df[col].dtype in ['float64', 'int64']:
                    self.df[col] = self.df[col].fillna(self.df[col].mean())
        elif strategy == 'fill_median':
            for col in columns:
                if self.df[col].dtype in ['float64', 'int64']:
                    self.df[col] = self.df[col].fillna(self.df[col].median())
        elif strategy == 'fill_mode':
            for col in columns:
                mode_val = self.df[col].mode()
                if len(mode_val) > 0:
                    self.df[col] = self.df[col].fillna(mode_val[0])
        elif strategy == 'fill_forward':
            self.df[columns] = self.df[columns].ffill()
        elif strategy == 'fill_backward':
            self.df[columns] = self.df[columns].bfill()
        elif strategy == 'fill_value':
            self.df[columns] = self.df[columns].fillna(fill_value)
        
        missing_after = self.df.isnull().sum().sum()
        self.log_action(f"Handled {missing_before - missing_after} missing values using '{strategy}' strategy")
        return self
    
    def remove_whitespace(self, columns=None):
        """
        Remove leading/trailing whitespace from string columns
        
        Args:
            columns: List of columns (None = all object columns)
            
        Returns:
            self (for method chaining)
        """
        if columns is None:
            columns = self.df.select_dtypes(include=['object']).columns
        
        for col in columns:
            if self.df[col].dtype == 'object':
                self.df[col] = self.df[col].str.strip()
        
        self.log_action(f"Removed whitespace from {len(columns)} columns")
        return self
    
    def standardize_case(self, columns, case='lower'):
        """
        Standardize text case
        
        Args:
            columns: List of column names
            case: 'lower', 'upper', 'title', 'capitalize'
            
        Returns:
            self (for method chaining)
        """
        for col in columns:
            if self.df[col].dtype == 'object':
                if case == 'lower':
                    self.df[col] = self.df[col].str.lower()
                elif case == 'upper':
                    self.df[col] = self.df[col].str.upper()
                elif case == 'title':
                    self.df[col] = self.df[col].str.title()
                elif case == 'capitalize':
                    self.df[col] = self.df[col].str.capitalize()
        
        self.log_action(f"Standardized case to '{case}' for {len(columns)} columns")
        return self
    
    def convert_data_types(self, column_types):
        """
        Convert column data types
        
        Args:
            column_types: dict like {'column_name': 'int64', 'another_col': 'float64'}
            
        Returns:
            self (for method chaining)
        """
        for col, dtype in column_types.items():
            try:
                self.df[col] = self.df[col].astype(dtype)
                self.log_action(f"Converted '{col}' to {dtype}")
            except Exception as e:
                print(f"❌ Error converting '{col}' to {dtype}: {e}")
        return self
    
    def remove_outliers(self, columns, method='iqr', threshold=1.5):
        """
        Remove outliers using IQR or Z-score method
        
        Args:
            columns: List of column names
            method: 'iqr' or 'zscore'
            threshold: IQR multiplier (1.5) or Z-score threshold (3)
            
        Returns:
            self (for method chaining)
        """
        initial_rows = len(self.df)
        
        for col in columns:
            if self.df[col].dtype in ['float64', 'int64']:
                if method == 'iqr':
                    Q1 = self.df[col].quantile(0.25)
                    Q3 = self.df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - threshold * IQR
                    upper_bound = Q3 + threshold * IQR
                    self.df = self.df[(self.df[col] >= lower_bound) & (self.df[col] <= upper_bound)]
                elif method == 'zscore':
                    z_scores = np.abs((self.df[col] - self.df[col].mean()) / self.df[col].std())
                    self.df = self.df[z_scores < threshold]
        
        removed = initial_rows - len(self.df)
        self.log_action(f"Removed {removed} outlier rows using {method} method")
        return self
    
    def standardize_values(self, column, mapping):
        """
        Standardize values in a column using a mapping dictionary
        
        Args:
            column: Column name
            mapping: dict like {'yes': 'Yes', 'no': 'No'}
            
        Returns:
            self (for method chaining)
        """
        self.df[column] = self.df[column].replace(mapping)
        self.log_action(f"Standardized values in '{column}' column")
        return self
    
    def rename_columns(self, column_mapping):
        """
        Rename columns
        
        Args:
            column_mapping: dict like {'old_name': 'new_name'}
            
        Returns:
            self (for method chaining)
        """
        self.df = self.df.rename(columns=column_mapping)
        self.log_action(f"Renamed {len(column_mapping)} columns")
        return self
    
    def drop_columns(self, columns):
        """
        Drop specified columns
        
        Args:
            columns: List of column names
            
        Returns:
            self (for method chaining)
        """
        self.df = self.df.drop(columns=columns, errors='ignore')
        self.log_action(f"Dropped {len(columns)} columns")
        return self
    
    def clip_values(self, column, lower=None, upper=None):
        """
        Clip values to a specified range
        
        Args:
            column: Column name
            lower: Lower bound
            upper: Upper bound
            
        Returns:
            self (for method chaining)
        """
        self.df[column] = self.df[column].clip(lower=lower, upper=upper)
        self.log_action(f"Clipped values in '{column}' to range [{lower}, {upper}]")
        return self
    
    def get_cleaning_summary(self):
        """
        Get summary of cleaning operations
        
        Returns:
            dict: Summary statistics
        """
        summary = {
            'original_shape': self.original_shape,
            'final_shape': self.df.shape,
            'rows_removed': self.original_shape[0] - self.df.shape[0],
            'columns_removed': self.original_shape[1] - self.df.shape[1],
            'cleaning_log': self.cleaning_log
        }
        return summary
    
    def get_cleaned_data(self):
        """
        Return cleaned DataFrame
        
        Returns:
            pandas.DataFrame: Cleaned data
        """
        return self.df