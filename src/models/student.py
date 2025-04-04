from dataclasses import dataclass
from typing import Optional


@dataclass
class Student:
    """Student data model for storing student information"""

    firstname: str
    middlename: str
    lastname: str
    age: int
    group: str
    notes: Optional[str] = None

    # TODO: Implement save logic to persist student data
    def save(self) -> bool:
        """Save student data to persistent storage

        Returns:
            bool: True if save was successful, False otherwise
        """
        # TODO: Implement save logic (database, sheets, etc.)
        return True

    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        """Create a Student instance from a dictionary

        Args:
            data: Dictionary containing student data

        Returns:
            Student: A new Student instance
        """
        return cls(**data)
