import json
import logging
from typing import Any, Dict, List, Optional

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Your existing SheetsService class (with minor logging addition) ---
# (I've added basic logging for clarity during operations)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SheetsService:
    """Service class for handling Google Sheets operations."""

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(
        self, credentials: Dict[str, Any], spreadsheet_id: Optional[str] = None
    ):
        """Initialize the sheets service."""
        self.creds = Credentials.from_service_account_info(
            credentials, scopes=self.SCOPES
        )
        self.service = build("sheets", "v4", credentials=self.creds)
        self.spreadsheet_id = spreadsheet_id
        logger.info(f"SheetsService initialized. Spreadsheet ID: {self.spreadsheet_id}")

    def create_spreadsheet(self, title: str) -> str:
        """Creates a new spreadsheet and returns its ID."""
        try:
            spreadsheet = {"properties": {"title": title}}
            result = (
                self.service.spreadsheets()
                .create(body=spreadsheet, fields="spreadsheetId")
                .execute()
            )
            self.spreadsheet_id = result["spreadsheetId"]
            logger.info(
                f"Created new spreadsheet '{title}' with ID: {self.spreadsheet_id}"
            )
            return self.spreadsheet_id
        except HttpError as e:
            error = json.loads(e.content)["error"]
            logger.error(f"Failed to create spreadsheet: {error.get('message')}")
            raise ValueError(f"Failed to create spreadsheet: {error.get('message')}")

    def create_sheet(self, title: str) -> str:
        """Create a new sheet within the spreadsheet."""
        if not self.spreadsheet_id:
            # If no spreadsheet ID, create one first
            self.create_spreadsheet("My ORM Spreadsheet")  # Default title
            logger.info(
                f"No spreadsheet ID provided, created new one: {self.spreadsheet_id}"
            )
            # The first sheet is already created with the spreadsheet, rename it
            try:
                requests = [
                    {
                        "updateSheetProperties": {
                            "properties": {"sheetId": 0, "title": title},
                            "fields": "title",
                        }
                    }
                ]
                body = {"requests": requests}
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id, body=body
                ).execute()
                logger.info(
                    f"Renamed initial sheet to '{title}' in spreadsheet {self.spreadsheet_id}"
                )
                return title
            except HttpError as e:
                error = json.loads(e.content)["error"]
                logger.error(f"Failed to rename initial sheet: {error.get('message')}")
                # Fallback to trying to add a sheet if renaming fails (maybe sheet 0 was deleted?)
                pass  # Continue to the addSheet logic below

        # If spreadsheet exists, add a new sheet
        try:
            body = {"requests": [{"addSheet": {"properties": {"title": title}}}]}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id, body=body
            ).execute()
            logger.info(f"Created sheet '{title}' in spreadsheet {self.spreadsheet_id}")
            return title

        except HttpError as e:
            error = json.loads(e.content)["error"]
            # Check if the error is because the sheet already exists
            if error.get("code") == 400 and "already exists" in error.get(
                "message", ""
            ):
                logger.warning(
                    f"Sheet '{title}' already exists in spreadsheet {self.spreadsheet_id}"
                )
                # Raise a specific, catchable error or just return the title
                # For ORM setup, just knowing it exists is fine.
                return title  # Indicate success or existence
            logger.error(f"Failed to create sheet: {error.get('message')}")
            raise ValueError(f"Failed to create sheet: {error.get('message')}")

    def get_all_sheets(self) -> List[str]:
        """Get all sheet names in the spreadsheet."""
        if not self.spreadsheet_id:
            logger.warning("Cannot get sheets, no spreadsheet_id set.")
            return []
        try:
            result = (
                self.service.spreadsheets()
                .get(spreadsheetId=self.spreadsheet_id)
                .execute()
            )
            return [sheet["properties"]["title"] for sheet in result.get("sheets", [])]
        except HttpError as e:
            logger.error(f"Failed to get sheets: {e}")
            return []

    def get_columns(self, sheet_name: str) -> List[str]:
        """Get column headers (first row) for the specified sheet."""
        if not self.spreadsheet_id:
            logger.warning(
                f"Cannot get columns for '{sheet_name}', no spreadsheet_id set."
            )
            return []
        try:
            result = (
                self.service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"'{sheet_name}'!1:1",  # Quote sheet name for safety
                )
                .execute()
            )

            if "values" not in result or not result["values"]:
                logger.info(
                    f"Sheet '{sheet_name}' appears to be empty or has no header row."
                )
                return []

            return result["values"][0]

        except HttpError as e:
            # Handle case where the sheet might exist but is empty or range is invalid
            error = json.loads(e.content)["error"]
            if error.get("code") == 400 and "Unable to parse range" in error.get(
                "message", ""
            ):
                logger.warning(
                    f"Sheet '{sheet_name}' might not exist or is inaccessible."
                )
                # Check if sheet actually exists
                if sheet_name not in self.get_all_sheets():
                    raise ValueError(f"Sheet '{sheet_name}' does not exist.")
                else:
                    # Sheet exists but is likely empty or inaccessible range
                    return []
            logger.error(f"Failed to get columns for '{sheet_name}': {e}")
            return []  # Or re-raise depending on desired strictness

    def add_columns(self, sheet_name: str, columns: List[str]) -> None:
        """Set or update the header row (columns) for the specified sheet."""
        if not self.spreadsheet_id:
            logger.error(
                f"Cannot add columns to '{sheet_name}', no spreadsheet_id set."
            )
            raise ValueError("Spreadsheet ID not set.")
        try:
            # Always overwrite/set the first row with the desired columns
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A1",  # Quote sheet name
                valueInputOption="RAW",
                body={"values": [columns]},
            ).execute()
            logger.info(f"Set columns for sheet '{sheet_name}': {columns}")

        except HttpError as e:
            error = json.loads(e.content)["error"]
            logger.error(
                f"Failed to add/update columns for '{sheet_name}': {error.get('message')}"
            )
            raise ValueError(f"Failed to add/update columns: {error.get('message')}")

    def append_row(self, sheet_name: str, row_values: List[Any]) -> None:
        """Append a list of values as a new row to the specified sheet."""
        if not self.spreadsheet_id:
            logger.error(f"Cannot append row to '{sheet_name}', no spreadsheet_id set.")
            raise ValueError("Spreadsheet ID not set.")
        try:
            # Ensure we append after the last row with data
            range_to_append = (
                f"'{sheet_name}'!A1"  # Append will find the first empty row
            )
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_to_append,
                valueInputOption="USER_ENTERED",  # Treat values as user would type them (numbers as numbers, etc.)
                insertDataOption="INSERT_ROWS",
                body={"values": [row_values]},  # Pass the list directly
            ).execute()
            logger.info(f"Appended row to sheet '{sheet_name}'")

        except HttpError as e:
            error = json.loads(e.content)["error"]
            logger.error(
                f"Failed to append row to '{sheet_name}': {error.get('message')}"
            )
            raise ValueError(f"Failed to append row: {error.get('message')}")

    def get_rows(self, sheet_name: str, start_row: int = 2) -> List[List[Any]]:
        """Get all data rows (as lists) from the specified sheet, starting from start_row."""
        if not self.spreadsheet_id:
            logger.warning(
                f"Cannot get rows for '{sheet_name}', no spreadsheet_id set."
            )
            return []
        try:
            # Use single quotes around sheet name in range
            range_name = f"'{sheet_name}'!A{start_row}:ZZ"
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range=range_name)
                .execute()
            )

            if "values" not in result:
                logger.info(
                    f"No data found in sheet '{sheet_name}' starting from row {start_row}."
                )
                return []

            return result["values"]

        except HttpError as e:
            # Handle case where the sheet might exist but range is invalid (e.g., empty sheet)
            error = json.loads(e.content)["error"]
            if error.get("code") == 400 and "Unable to parse range" in error.get(
                "message", ""
            ):
                logger.warning(
                    f"Sheet '{sheet_name}' might not exist or range is invalid."
                )
                # Check if sheet actually exists
                if sheet_name not in self.get_all_sheets():
                    raise ValueError(f"Sheet '{sheet_name}' does not exist.")
                else:
                    # Sheet exists but is likely empty or inaccessible range
                    return []
            logger.error(f"Failed to get rows for '{sheet_name}': {e}")
            return []

    def update_row(
        self, sheet_name: str, row_index: int, row_values: List[Any]
    ) -> None:
        """Updates a specific row (1-based index) with new values."""
        if not self.spreadsheet_id:
            logger.error(f"Cannot update row in '{sheet_name}', no spreadsheet_id set.")
            raise ValueError("Spreadsheet ID not set.")
        if row_index < 1:
            raise ValueError("Row index must be 1-based.")

        try:
            # Range for the specific row to update
            range_name = (
                f"'{sheet_name}'!A{row_index}:ZZ{row_index}"  # Quote sheet name
            )

            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",  # Treat values as user would type them
                body={"values": [row_values]},  # Pass the list directly
            ).execute()
            logger.info(f"Updated row {row_index} in sheet '{sheet_name}'")

        except HttpError as e:
            error = json.loads(e.content)["error"]
            logger.error(
                f"Failed to update row {row_index} in '{sheet_name}': {error.get('message')}"
            )
            raise ValueError(f"Failed to update row: {error.get('message')}")

    def freeze_rows(self, sheet_name: str, rows: int) -> None:
        """Freeze the specified number of rows in a sheet."""
        if not self.spreadsheet_id:
            logger.error(
                f"Cannot freeze rows in '{sheet_name}', no spreadsheet_id set."
            )
            raise ValueError("Spreadsheet ID not set.")
        try:
            sheet_id = self._get_sheet_id(sheet_name)
            if sheet_id is None:
                logger.error(f"Sheet '{sheet_name}' not found, cannot freeze rows.")
                raise ValueError(f"Sheet '{sheet_name}' not found.")

            request = {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {"frozenRowCount": rows},
                    },
                    "fields": "gridProperties.frozenRowCount",
                }
            }
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id, body={"requests": [request]}
            ).execute()
            logger.info(f"Froze {rows} row(s) in sheet '{sheet_name}'")
        except HttpError as e:
            error = json.loads(e.content)["error"]
            logger.error(
                f"Error freezing rows in '{sheet_name}': {error.get('message')}"
            )
            raise ValueError(f"Error freezing rows: {error.get('message')}")
        except Exception as e:
            logger.error(f"Unexpected error freezing rows in '{sheet_name}': {e}")
            raise

    def _get_sheet_id(self, sheet_name: str) -> Optional[int]:
        """Helper to get the numeric ID of a sheet by its name."""
        if not self.spreadsheet_id:
            return None
        try:
            result = (
                self.service.spreadsheets()
                .get(
                    spreadsheetId=self.spreadsheet_id,
                    fields="sheets(properties(sheetId,title))",
                )
                .execute()
            )
            for sheet in result.get("sheets", []):
                if sheet["properties"]["title"] == sheet_name:
                    return sheet["properties"]["sheetId"]
            return None
        except HttpError:
            return None
