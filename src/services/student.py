import json
import logging
from dataclasses import dataclass
from typing import Optional

from googleapiclient.errors import HttpError

from src.config.config import BotConfig
from src.config.load_config import load_config
from src.services.sheet_orm import SheetORM
from src.services.sheets_service import SheetsService

# --- Your existing SheetsService class (with minor logging addition) ---
# (I've added basic logging for clarity during operations)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 1. Define your data model using dataclasses
@dataclass
class Student:
    __pk__ = "student_id"  # Define the primary key attribute name

    student_id: str
    name: str
    major: str
    graduation_year: Optional[int] = None  # Optional field


def create_student_orm() -> SheetORM:
    config: BotConfig = load_config()
    # 2. Prepare Credentials and Spreadsheet ID
    # Replace with your actual credentials file path and spreadsheet ID
    # If spreadsheet_id is None, the service will create a new spreadsheet.
    try:
        with open("./credentials.json", "r") as f:
            google_credentials = json.load(f)
    except FileNotFoundError:
        print("ERROR: Service account file not found. Please update the path.")
        exit()
    except json.JSONDecodeError:
        print("ERROR: Service account file is not valid JSON.")
        exit()

    # Optional: Specify an existing Spreadsheet ID, otherwise a new one might be created.
    # SPREADSHEET_ID = "YOUR_EXISTING_SPREADSHEET_ID"
    SPREADSHEET_ID = config.SHEET_ID  # Let the service create one if needed

    # 3. Initialize the services
    sheets_service = SheetsService(
        credentials=google_credentials, spreadsheet_id=SPREADSHEET_ID
    )

    # If a new spreadsheet was created, update the SPREADSHEET_ID variable
    # (The SheetORM init needs the service to know the spreadsheet ID)
    if SPREADSHEET_ID is None and sheets_service.spreadsheet_id:
        SPREADSHEET_ID = sheets_service.spreadsheet_id
        print(f"New spreadsheet created with ID: {SPREADSHEET_ID}")

    # Check if we have a spreadsheet ID now before proceeding
    if not sheets_service.spreadsheet_id:
        print("ERROR: Failed to obtain a Spreadsheet ID. Cannot initialize ORM.")
        exit()

    # 4. Initialize the ORM for your model
    try:
        return SheetORM(service=sheets_service, model_cls=Student)

    #     # 5. Use the ORM
    #     print("\n--- ORM Operations ---")

    #     # Create and save new students
    #     print("Saving new students...")
    #     student1 = Student(
    #         student_id="S1001",
    #         name="Alice Smith",
    #         major="Computer Science",
    #         graduation_year=2025,
    #     )
    #     student2 = Student(
    #         student_id="S1002", name="Bob Johnson", major="Physics"
    #     )  # Optional year is None
    #     student_orm.save(student1)
    #     student_orm.save(student2)
    #     print("Students saved.")

    #     # Get a specific student
    #     print("\nGetting student S1001...")
    #     retrieved_student = student_orm.get("S1001")
    #     if retrieved_student:
    #         print(f"Found: {retrieved_student}")
    #         # Update the student
    #         retrieved_student.major = "Data Science"
    #         retrieved_student.graduation_year = 2026
    #         print("Updating student S1001...")
    #         student_orm.update(retrieved_student)
    #         print("Student updated.")
    #     else:
    #         print("Student S1001 not found.")

    #     # Try getting a non-existent student
    #     print("\nGetting student S9999...")
    #     non_existent = student_orm.get("S9999")
    #     print(f"Found: {non_existent}")

    #     # Get all students
    #     print("\nGetting all students...")
    #     all_students = student_orm.get_all()
    #     for s in all_students:
    #         print(s)

    except (TypeError, ValueError, RuntimeError, HttpError) as e:
        print(f"\nAn error occurred: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
