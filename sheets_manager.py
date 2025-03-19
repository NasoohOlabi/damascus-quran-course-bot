import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from Levenshtein import distance

load_dotenv()

class Table:
    """Represents a table (sheet) in the Google Sheets document."""
    
    def __init__(self, name: str, columns: List[str]):
        self.name = name
        self.columns = columns
        self._column_index = {col.lower(): idx for idx, col in enumerate(columns)}

    def get_column_index(self, column: str) -> int:
        """Get the index of a column by its name."""
        column = column.lower()
        if column not in self._column_index:
            raise ValueError(f"Column '{column}' not found in table '{self.name}'")
        return self._column_index[column]

    def has_column(self, column: str) -> bool:
        """Check if a column exists."""
        return column.lower() in self._column_index

    def add_column(self, column: str) -> None:
        """Add a new column."""
        if self.has_column(column):
            return
        self.columns.append(column)
        self._column_index[column.lower()] = len(self.columns) - 1

    def get_range(self, columns: Optional[List[str]] = None) -> str:
        """Get the A1 notation range for specified columns or all columns."""
        if not columns:
            return f"{self.name}!A:Z"
        indices = [self.get_column_index(col) for col in columns]
        cols = [chr(65 + i) for i in indices]  # Convert to A1 notation
        return f"{self.name}!{cols[0]}:{cols[-1]}"

class SheetsManager:
    """A middleware class to simplify interactions with Google Sheets."""
    
    def __init__(self, credentials_path: str = 'credentials.json'):
        """Initialize the SheetsManager with Google Sheets credentials."""
        self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        self.SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
        
        if not self.SHEET_ID:
            raise ValueError("GOOGLE_SHEET_ID not found in environment variables")
            
        credentials = Credentials.from_service_account_file(
            credentials_path, scopes=self.SCOPES
        )
        self.service = build('sheets', 'v4', credentials=credentials)
        self.sheet = self.service.spreadsheets()
        self.tables: Dict[str, Table] = {}

    def get_all_sheets(self) -> List[str]:
        """Get all sheet names in the spreadsheet."""
        spreadsheet = self.sheet.get(spreadsheetId=self.SHEET_ID).execute()
        return [sheet['properties']['title'] for sheet in spreadsheet['sheets']]

    def create_sheet(self, name: str) -> None:
        """Create a new sheet with the given name."""
        body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': name
                    }
                }
            }]
        }
        self.sheet.batchUpdate(
            spreadsheetId=self.SHEET_ID,
            body=body
        ).execute()

    def init_table(self, name: str) -> Table:
        """Initialize a table by reading its header row."""
        range_name = f"{name}!A1:Z1"
        result = self.sheet.values().get(
            spreadsheetId=self.SHEET_ID,
            range=range_name
        ).execute()
        
        values = result.get('values', [[]])[0]
        table = Table(name, values if values != [''] else [])
        self.tables[name] = table
        return table

    def get_table(self, name: str) -> Table:
        """Get a table by name, initializing it if necessary."""
        if name not in self.tables:
            return self.init_table(name)
        return self.tables[name]

    def add_columns(self, table_name: str, columns: List[str]) -> None:
        """Add new columns to a table."""
        table = self.get_table(table_name)
        current_range = f"{table_name}!A1:{chr(65 + len(table.columns))}"
        
        # Get current headers
        result = self.sheet.values().get(
            spreadsheetId=self.SHEET_ID,
            range=current_range
        ).execute()
        current_headers = result.get('values', [[]])[0]
        
        # Add new columns
        new_headers = current_headers.copy()
        for col in columns:
            if col not in new_headers:
                new_headers.append(col)
                table.add_column(col)
        
        # Update headers if changed
        if len(new_headers) > len(current_headers):
            self.write_range(f"{table_name}!A1", [new_headers])

    def search_column(self, table_name: str, column: str, value: Any, exact: bool = True) -> List[Dict[str, Any]]:
        """
        Search for rows where the specified column matches the value.
        
        Args:
            table_name: Name of the table (sheet) to search in
            column: Name of the column to search in
            value: Value to search for
            exact: If True, perform exact match; if False, use fuzzy matching
        
        Returns:
            List of matching rows as dictionaries
        """
        table = self.get_table(table_name)
        values = self.read_range(table.get_range())
        
        if not values:
            return []

        results = []
        col_idx = table.get_column_index(column)
        
        for row in values[1:]:  # Skip header row
            if len(row) <= col_idx:
                continue
                
            row_value = str(row[col_idx])
            match = False
            
            if exact:
                match = row_value == str(value)
            else:
                # Fuzzy match using Levenshtein distance
                # Match if distance is less than 30% of the length of the longer string
                max_distance = max(len(str(value)), len(row_value)) * 0.3
                match = distance(str(value), row_value) <= max_distance

            if match:
                # Create a dictionary with column names as keys
                row_dict = {}
                for i, col in enumerate(table.columns):
                    row_dict[col] = row[i] if i < len(row) else None
                results.append(row_dict)

        return results

    def fuzzy_search_column(self, table_name: str, column: str, value: str, 
                          max_distance: Optional[int] = None) -> List[Tuple[Dict[str, Any], int]]:
        """
        Search for rows using Levenshtein distance, returning results sorted by similarity.
        
        Args:
            table_name: Name of the table (sheet) to search in
            column: Name of the column to search in
            value: Value to search for
            max_distance: Maximum Levenshtein distance to consider (optional)
        
        Returns:
            List of tuples containing (row_dict, distance) sorted by distance
        """
        table = self.get_table(table_name)
        values = self.read_range(table.get_range())
        
        if not values:
            return []

        results = []
        col_idx = table.get_column_index(column)
        
        for row in values[1:]:  # Skip header row
            if len(row) <= col_idx:
                continue
                
            row_value = str(row[col_idx])
            dist = distance(str(value), row_value)
            
            if max_distance is None or dist <= max_distance:
                # Create a dictionary with column names as keys
                row_dict = {}
                for i, col in enumerate(table.columns):
                    row_dict[col] = row[i] if i < len(row) else None
                results.append((row_dict, dist))

        # Sort by distance (closest matches first)
        return sorted(results, key=lambda x: x[1])

    def read_range(self, range_name: str) -> List[List[Any]]:
        """Read data from a specified range in the sheet."""
        result = self.sheet.values().get(
            spreadsheetId=self.SHEET_ID,
            range=range_name
        ).execute()
        return result.get('values', [])

    def write_range(self, range_name: str, values: List[List[Any]]) -> None:
        """Write data to a specified range in the sheet."""
        body = {'values': values}
        self.sheet.values().update(
            spreadsheetId=self.SHEET_ID,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()

    def append_row(self, table_name: str, row_data: Dict[str, Any]) -> None:
        """
        Append a single row of data to the specified table.
        
        Args:
            table_name: Name of the table (sheet) to append to
            row_data: Dictionary mapping column names to values
        """
        table = self.get_table(table_name)
        
        # Check for new columns
        new_columns = []
        for col in row_data.keys():
            if not table.has_column(col):
                new_columns.append(col)
        
        # Add new columns if needed
        if new_columns:
            self.add_columns(table_name, new_columns)
            table = self.get_table(table_name)  # Refresh table with new columns
        
        # Convert dictionary to list in correct column order
        row_values = []
        for col in table.columns:
            row_values.append(row_data.get(col, ''))
        
        body = {'values': [row_values]}
        self.sheet.values().append(
            spreadsheetId=self.SHEET_ID,
            range=f"{table_name}!A:A",
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()

    def clear_range(self, range_name: str) -> None:
        """Clear data from a specified range in the sheet."""
        self.sheet.values().clear(
            spreadsheetId=self.SHEET_ID,
            range=range_name
        ).execute()

    def update_row(self, table_name: str, search_column: str, search_value: Any, 
                  new_data: Dict[str, Any], exact: bool = True) -> bool:
        """
        Update a row where the specified column matches the search value.
        
        Args:
            table_name: Name of the table (sheet) to update
            search_column: Name of the column to search in
            search_value: Value to search for
            new_data: Dictionary mapping column names to new values
            exact: If True, perform exact match; if False, use fuzzy matching
        
        Returns:
            True if a row was updated, False otherwise
        """
        matches = self.search_column(table_name, search_column, search_value, exact=exact)
        if not matches:
            return False
            
        # Update the first matching row
        table = self.get_table(table_name)
        values = self.read_range(table.get_range())
        search_idx = table.get_column_index(search_column)
        
        for i, row in enumerate(values[1:], 1):  # Skip header row
            if len(row) <= search_idx:
                continue
                
            row_value = str(row[search_idx])
            match = False
            
            if exact:
                match = row_value == str(search_value)
            else:
                max_distance = max(len(str(search_value)), len(row_value)) * 0.3
                match = distance(str(search_value), row_value) <= max_distance

            if match:
                # Convert dictionary to list in correct column order
                new_row = [new_data.get(col, row[idx]) if idx < len(row) else new_data.get(col)
                          for idx, col in enumerate(table.columns)]
                self.write_range(f"{table_name}!A{i+1}", [new_row])
                return True
                
        return False

    def get_columns(self, table_name: str) -> List[str]:
        """Get all column names for a table."""
        table = self.get_table(table_name)
        return table.columns.copy() 