import json
from typing import Any, Dict, List, Optional

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class SheetsService:
    """Service class for handling Google Sheets operations."""
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(self, credentials: Dict[str, Any], spreadsheet_id: Optional[str] = None):
        """Initialize the sheets service."""
        self.creds = Credentials.from_service_account_info(credentials, scopes=self.SCOPES)
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.spreadsheet_id = spreadsheet_id
        
    def create_sheet(self, title: str) -> str:
        """Create a new sheet with the given title."""
        try:
            # If no spreadsheet ID exists, create a new spreadsheet
            if not self.spreadsheet_id:
                spreadsheet = {
                    'properties': {
                        'title': 'Makin Damascus Data'
                    },
                    'sheets': [{
                        'properties': {
                            'title': title
                        }
                    }]
                }
                
                result = self.service.spreadsheets().create(
                    body=spreadsheet
                ).execute()
                
                self.spreadsheet_id = result['spreadsheetId']
                return title
                
            # If spreadsheet exists, add a new sheet
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': title
                        }
                    }
                }]
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            return title
            
        except HttpError as e:
            error = json.loads(e.content)['error']
            if error.get('code') == 400 and 'already exists' in error.get('message', ''):
                raise ValueError(f"Sheet '{title}' already exists")
            raise ValueError(f"Failed to create sheet: {error.get('message')}")
    
    def get_all_sheets(self) -> List[str]:
        """Get all sheet names in the spreadsheet."""
        try:
            if not self.spreadsheet_id:
                return []
                
            result = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            return [sheet['properties']['title'] for sheet in result['sheets']]
            
        except HttpError:
            return []
    
    def get_columns(self, sheet_name: str) -> List[str]:
        """Get column headers for the specified sheet."""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{sheet_name}!1:1'
            ).execute()
            
            if 'values' not in result:
                return []
                
            return result['values'][0]
            
        except HttpError:
            return []
    
    def add_columns(self, sheet_name: str, columns: List[str]) -> None:
        """Add new columns to the specified sheet."""
        try:
            current_columns = self.get_columns(sheet_name)
            
            # If sheet is empty, just add the columns
            if not current_columns:
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{sheet_name}!A1',
                    valueInputOption='RAW',
                    body={'values': [columns]}
                ).execute()
                return
            
            # Add new columns to existing ones
            new_columns = current_columns.copy()
            for column in columns:
                if column not in new_columns:
                    new_columns.append(column)
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f'{sheet_name}!A1',
                valueInputOption='RAW',
                body={'values': [new_columns]}
            ).execute()
            
        except HttpError as e:
            error = json.loads(e.content)['error']
            raise ValueError(f"Failed to add columns: {error.get('message')}")
    
    def append_row(self, sheet_name: str, data: Dict[str, Any]) -> None:
        """Append a row of data to the specified sheet."""
        try:
            columns = self.get_columns(sheet_name)
            if not columns:
                raise ValueError("Sheet has no columns")
            
            # Create row with values in correct order
            row = []
            for column in columns:
                row.append(data.get(column, ''))
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f'{sheet_name}!A1',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [row]}
            ).execute()
            
        except HttpError as e:
            error = json.loads(e.content)['error']
            raise ValueError(f"Failed to append row: {error.get('message')}")
    
    def get_rows(self, sheet_name: str, start_row: int = 2) -> List[Dict[str, Any]]:
        """Get all rows from the specified sheet."""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{sheet_name}!A{start_row}:ZZ'
            ).execute()
            
            if 'values' not in result:
                return []
            
            columns = self.get_columns(sheet_name)
            rows = []
            
            for row_values in result['values']:
                row_data = {}
                for i, value in enumerate(row_values):
                    if i < len(columns):
                        row_data[columns[i]] = value
                rows.append(row_data)
            
            return rows
            
        except HttpError:
            return []
