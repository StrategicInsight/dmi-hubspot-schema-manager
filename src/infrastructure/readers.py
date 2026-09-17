"""Source readers: turn a spreadsheet file into domain model lists."""
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

from domain.models import AssociationDefinition, ObjectSchemaDefinition, PropertyDefinition

OBJECT_SHEET_NAMES = ("objects", "schemas", "custom_objects")
ASSOCIATION_SHEET_NAMES = ("associations", "association_labels", "labels")
PROPERTY_SHEET_NAMES = ("properties", "fields", "attributes")


class SourceReader(ABC):
    """Abstract base class for reading HubSpot import data."""

    @abstractmethod
    def read_objects(self) -> list[ObjectSchemaDefinition]:
        """Read object schema definitions from the source.""" 

    @abstractmethod
    def read_associations(self) -> list[AssociationDefinition]:
        """Read association definitions from the source."""

    @abstractmethod
    def read_properties(self) -> dict[str, list[PropertyDefinition]]:
        """Read property definitions grouped by object type."""


def _properties_by_object(
    df: pd.DataFrame,
    sheet_label: str
) -> dict[str, list[PropertyDefinition]]:
    """Build property definitions grouped by object type from a DataFrame."""

    if "object" not in df.columns:
        print(f"[WARN] No 'object' column found in properties sheet '{sheet_label}'.")
        return {}
    return {
        str(object_type): [
            PropertyDefinition.from_row(
                str(object_type),
                row,
            )
            for row in group.to_dict(orient="records")
        ]
        for object_type, group in df.groupby("object")
    }


class ExcelSourceReader(SourceReader):
    """Reads HubSpot definitions from an Excel workbook."""

    def __init__(self, file_path: Path):
        """Initialize the reader with an Excel file."""

        self._file_path = file_path
        self._workbook = pd.ExcelFile(file_path)
        self._sheet_map = {
            str(name).strip().lower(): str(name)
            for name in self._workbook.sheet_names
        }

    def _find_sheet(self, candidates: tuple[str, ...]) -> str | None:
        """Find the first matching worksheet from a list of candidates."""

        for candidate in candidates:
            normalized_name = candidate.strip().lower()
            sheet = self._sheet_map.get(normalized_name)
            if sheet is not None:
                return sheet
        return None

    def read_objects(self) -> list[ObjectSchemaDefinition]:
        """Read object schema definitions from the workbook."""

        sheet = self._find_sheet(OBJECT_SHEET_NAMES)
        if sheet is None:
            return []
        df = pd.read_excel(self._file_path, sheet_name=sheet)
        return [
            ObjectSchemaDefinition.from_row(row.to_dict())
            for _, row in df.iterrows()
            if pd.notna(row.get("name"))
        ]

    def read_associations(self) -> list[AssociationDefinition]:
        """Read association definitions from the workbook."""

        sheet = self._find_sheet(ASSOCIATION_SHEET_NAMES)
        if not sheet:
            return []
        df = pd.read_excel(self._file_path, sheet_name=sheet)
        return [
            AssociationDefinition.from_row(row.to_dict())
            for _, row in df.iterrows()
        ]

    def read_properties(self) -> dict[str, list[PropertyDefinition]]:
        """Read property definitions from the workbook."""

        sheet = self._find_sheet(PROPERTY_SHEET_NAMES)
        if sheet is None:
            sheet = str(self._workbook.sheet_names[0])
        df = pd.read_excel(self._file_path, sheet_name=sheet)
        return _properties_by_object(df, sheet)


class CsvSourceReader(SourceReader):
    """Reads HubSpot definitions from a CSV file."""

    def __init__(self, file_path: Path):
        """Initialize the reader with a CSV file."""
        self._df = pd.read_csv(file_path)

    def read_objects(self) -> list[ObjectSchemaDefinition]:
        """Read object schema definitions from the CSV file."""
        return []

    def read_associations(self) -> list[AssociationDefinition]:
        """Read association definitions from the CSV file."""

        if "fromObject" not in self._df.columns or "toObject" not in self._df.columns:
            return []
        return [
            AssociationDefinition.from_row(row.to_dict())
            for _, row in self._df.iterrows()
        ]

    def read_properties(self) -> dict[str, list[PropertyDefinition]]:
        """Read property definitions from the CSV file."""

        if "fromObject" in self._df.columns and "toObject" in self._df.columns:
            return {}
        return _properties_by_object(self._df, "csv")


def create_reader(file_path: Path) -> SourceReader:
    """Create a source reader based on the file type."""

    suffix = file_path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        return ExcelSourceReader(file_path)
    if suffix == ".csv":
        return CsvSourceReader(file_path)
    raise ValueError(f"Unsupported file type: {suffix}")
