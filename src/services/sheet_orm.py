import logging
from dataclasses import asdict, fields
from typing import Any, List, Optional, Type, TypeVar

from googleapiclient.errors import HttpError

from .sheets_service import SheetsService

# --- Your existing SheetsService class (with minor logging addition) ---
# (I've added basic logging for clarity during operations)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar("T")  # Generic type for model instances


class SheetORM:
    """
    ORM-like wrapper for Google Sheets using dataclasses.

    Manages a specific sheet corresponding to a dataclass model.
    Handles creation, retrieval, update of rows as model instances.
    """

    def __init__(self, service: SheetsService, model_cls: Type[T]):
        """
        Initialize the ORM for a specific model and sheet.

        Args:
            service: An initialized SheetsService instance.
            model_cls: The dataclass type to map to the sheet.
                       Must have a `__pk__` class attribute specifying the primary key field name.
                       Must be decorated with @dataclass.
        """
        if not hasattr(model_cls, "__dataclass_fields__"):
            raise TypeError(f"{model_cls.__name__} must be a dataclass.")
        if not hasattr(model_cls, "__pk__") or not isinstance(model_cls.__pk__, str):
            raise TypeError(
                f"{model_cls.__name__} must have a string class attribute '__pk__'."
            )

        self.service = service
        self.model_cls = model_cls
        self.sheet_name = (
            model_cls.__name__ + "s"
        )  # Simple pluralization for sheet name
        self.fields = fields(model_cls)
        self.columns = [f.name for f in self.fields]
        self.pk_field = model_cls.__pk__

        if self.pk_field not in self.columns:
            raise ValueError(
                f"Primary key '{self.pk_field}' defined in {model_cls.__name__}.__pk__ not found in dataclass fields."
            )

        logger.info(
            f"Initializing SheetORM for model {model_cls.__name__} -> sheet '{self.sheet_name}'"
        )
        self._ensure_sheet_and_columns()

    def _ensure_sheet_and_columns(self):
        """Checks if the sheet exists and has the correct columns, creating/updating if necessary."""
        all_sheets = self.service.get_all_sheets()
        if self.sheet_name not in all_sheets:
            logger.info(f"Sheet '{self.sheet_name}' not found. Creating...")
            self.service.create_sheet(self.sheet_name)
            self.service.add_columns(self.sheet_name, self.columns)
            self.service.freeze_rows(self.sheet_name, 1)  # Freeze header row
            logger.info(
                f"Sheet '{self.sheet_name}' created with columns: {self.columns}"
            )
        else:
            logger.info(f"Sheet '{self.sheet_name}' found. Verifying columns...")
            current_columns = self.service.get_columns(self.sheet_name)
            if current_columns != self.columns:
                # This implementation chooses to overwrite columns if they don't match exactly.
                # You might want different logic (e.g., only adding missing ones).
                logger.warning(
                    f"Columns mismatch in '{self.sheet_name}'. Expected: {self.columns}, Found: {current_columns}. Overwriting header."
                )
                self.service.add_columns(self.sheet_name, self.columns)
                self.service.freeze_rows(self.sheet_name, 1)  # Re-freeze header row
            else:
                logger.info(
                    f"Columns in '{self.sheet_name}' match model {self.model_cls.__name__}."
                )

    def _instance_to_row_list(self, instance: T) -> List[Any]:
        """Converts a model instance to a list of values in column order."""
        if not isinstance(instance, self.model_cls):
            raise TypeError(
                f"Expected instance of {self.model_cls.__name__}, got {type(instance).__name__}"
            )
        instance_dict = asdict(instance)
        # Ensure order matches self.columns
        return [instance_dict.get(col_name, None) for col_name in self.columns]

    def _row_list_to_instance(self, row_values: List[Any]) -> T:
        """Converts a list of values from a sheet row into a model instance."""
        # Pad row_values with None if it's shorter than columns (e.g., empty trailing cells)
        padded_values = row_values + [None] * (len(self.columns) - len(row_values))
        row_dict = dict(zip(self.columns, padded_values))

        # Attempt to construct the dataclass instance
        # Note: This doesn't handle type conversion automatically.
        # Google Sheets API often returns strings. You might need
        # specific converters if your dataclass has int, float, bool etc.
        # For simplicity, this basic version passes values as is.
        try:
            # Filter out unexpected keys if any (though zip should prevent this)
            valid_keys = {f.name for f in self.fields}
            filtered_dict = {k: v for k, v in row_dict.items() if k in valid_keys}
            # Add Nones for missing keys expected by the dataclass
            for field in self.fields:
                if field.name not in filtered_dict:
                    filtered_dict[field.name] = None

            # Basic type coercion attempt (can be expanded)
            coerced_dict = {}
            for field in self.fields:
                key = field.name
                value = filtered_dict.get(key)
                target_type = field.type
                if value is not None:
                    try:
                        if target_type == bool:
                            coerced_dict[key] = str(value).upper() in (
                                "TRUE",
                                "1",
                                "YES",
                            )
                        elif target_type == int:
                            coerced_dict[key] = int(value)
                        elif target_type == float:
                            coerced_dict[key] = float(value)
                        else:  # Keep as string or original type if complex
                            coerced_dict[key] = value
                    except (ValueError, TypeError):
                        logger.warning(
                            f"Could not coerce value '{value}' to type {target_type} for field '{key}'. Keeping original."
                        )
                        coerced_dict[key] = value  # Keep original if coercion fails
                else:
                    coerced_dict[key] = None

            return self.model_cls(**coerced_dict)
        except TypeError as e:
            logger.error(
                f"Failed to create instance of {self.model_cls.__name__} from row data: {row_dict}. Error: {e}"
            )
            raise ValueError(
                f"Could not create {self.model_cls.__name__} instance: {e}"
            )

    def save(self, instance: T) -> T:
        """
        Appends a new row to the sheet based on the instance data.
        Assumes the instance does not already exist. Use update() for existing records.

        Returns:
            The saved instance.
        """
        logger.info(
            f"Saving new {self.model_cls.__name__} instance to sheet '{self.sheet_name}'..."
        )
        row_values = self._instance_to_row_list(instance)
        self.service.append_row(self.sheet_name, row_values)
        logger.info(f"{self.model_cls.__name__} instance saved successfully.")
        return instance  # Return the original instance

    def _find_row_index_by_pk(self, pk_value: Any) -> Optional[int]:
        """Finds the 1-based row index of the row matching the primary key value."""
        try:
            pk_col_index = self.columns.index(self.pk_field)
        except ValueError:
            # This should not happen if __init__ checks passed
            raise RuntimeError(
                f"PK field '{self.pk_field}' not found in derived columns."
            )

        all_rows = self.service.get_rows(
            self.sheet_name, start_row=2
        )  # Data rows start at 2
        pk_value_str = str(pk_value)  # Compare as strings for simplicity from sheets

        for i, row in enumerate(all_rows):
            if len(row) > pk_col_index and str(row[pk_col_index]) == pk_value_str:
                # Return the 1-based sheet row index (+2 because get_rows starts at 2)
                return i + 2
        return None

    def update(self, instance: T) -> T:
        """
        Updates an existing row in the sheet identified by the instance's primary key.

        Raises:
            ValueError: If no row is found with the instance's primary key.

        Returns:
            The updated instance.
        """
        if not isinstance(instance, self.model_cls):
            raise TypeError(
                f"Expected instance of {self.model_cls.__name__}, got {type(instance).__name__}"
            )

        pk_value = getattr(instance, self.pk_field)
        if pk_value is None:
            raise ValueError(
                "Instance must have a non-None primary key value for update."
            )

        logger.info(
            f"Attempting to update {self.model_cls.__name__} with PK '{pk_value}' in sheet '{self.sheet_name}'..."
        )

        row_index = self._find_row_index_by_pk(pk_value)

        if row_index is None:
            logger.error(
                f"Cannot update: No row found with PK '{pk_value}' in sheet '{self.sheet_name}'."
            )
            raise ValueError(
                f"No {self.model_cls.__name__} found with {self.pk_field}={pk_value} to update."
            )

        row_values = self._instance_to_row_list(instance)
        self.service.update_row(self.sheet_name, row_index, row_values)
        logger.info(
            f"{self.model_cls.__name__} with PK '{pk_value}' updated successfully at row {row_index}."
        )
        return instance

    def get(self, pk_value: Any) -> Optional[T]:
        """
        Retrieves a single instance from the sheet by its primary key.

        Args:
            pk_value: The primary key value to search for.

        Returns:
            The matching model instance, or None if not found.
        """
        logger.info(
            f"Getting {self.model_cls.__name__} with PK '{pk_value}' from sheet '{self.sheet_name}'..."
        )
        row_index = self._find_row_index_by_pk(pk_value)

        if row_index is None:
            logger.info(f"No {self.model_cls.__name__} found with PK '{pk_value}'.")
            return None

        # Fetch the specific row data again to be sure (or reuse if confident)
        # Range for the specific row
        range_name = (
            f"'{self.sheet_name}'!A{row_index}:ZZ{row_index}"  # Quote sheet name
        )
        try:
            result = (
                self.service.service.spreadsheets()
                .values()
                .get(spreadsheetId=self.service.spreadsheet_id, range=range_name)
                .execute()
            )

            if "values" not in result or not result["values"]:
                # Should not happen if _find_row_index_by_pk found it, but defensive check
                logger.error(
                    f"Inconsistency: Found PK '{pk_value}' at row {row_index}, but failed to re-fetch row data."
                )
                return None

            row_values = result["values"][0]
            instance = self._row_list_to_instance(row_values)
            logger.info(
                f"Successfully retrieved {self.model_cls.__name__} with PK '{pk_value}'."
            )
            return instance

        except HttpError as e:
            logger.error(f"Failed to get row {row_index} for PK '{pk_value}': {e}")
            return None

    def next_pk(self) -> str:
        pass

    def get_all(self) -> List[T]:
        """
        Retrieves all data rows from the sheet and converts them into model instances.

        Returns:
            A list of model instances.
        """
        logger.info(
            f"Getting all {self.model_cls.__name__} instances from sheet '{self.sheet_name}'..."
        )
        all_row_values = self.service.get_rows(
            self.sheet_name, start_row=2
        )  # Data starts row 2
        instances = []
        for i, row_values in enumerate(all_row_values):
            try:
                instances.append(self._row_list_to_instance(row_values))
            except ValueError as e:
                # Log error for the specific row and continue if possible
                logger.error(
                    f"Skipping row {i + 2}: Could not convert row data to {self.model_cls.__name__}. Data: {row_values}. Error: {e}"
                )
            except Exception as e:
                logger.error(
                    f"Skipping row {i + 2}: Unexpected error converting row data. Data: {row_values}. Error: {e}"
                )

        logger.info(f"Retrieved {len(instances)} {self.model_cls.__name__} instances.")
        return instances
        return instances
