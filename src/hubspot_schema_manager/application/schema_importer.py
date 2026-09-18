"""Orchestrates the import: reads definitions from a source and syncs them to HubSpot."""
from hubspot_schema_manager.infrastructure.readers import SourceReader
from hubspot_schema_manager.infrastructure.repositories import (
    AssociationRepository,
    PropertyRepository,
    SchemaRepository
)


class SchemaImporter:
    """Coordinate the import of HubSpot definitions."""

    def __init__(
        self,
        reader: SourceReader,
        schema_repo: SchemaRepository,
        association_repo: AssociationRepository,
        property_repo: PropertyRepository,
    ) -> None:
        """Initialize the importer with its required dependencies."""

        self._reader = reader
        self._schema_repo = schema_repo
        self._association_repo = association_repo
        self._property_repo = property_repo

    def run(self) -> None:
        """Run all HubSpot import operations."""

        self._import_objects()
        self._import_associations()
        self._import_properties()

    def _import_objects(self) -> None:
        """Import object schema definitions."""

        objects = self._reader.read_objects()
        if not objects:
            return
        print(f"\n[INFO] Found {len(objects)} object definitions.")
        existing = self._schema_repo.get_existing()
        for schema in objects:
            self._schema_repo.create(schema, existing)

    def _import_associations(self) -> None:
        """Import association definitions."""

        associations = self._reader.read_associations()
        if not associations:
            return
        print(f"\n[INFO] Found {len(associations)} association definitions.")
        for association in associations:
            if not association.is_valid:
                print(f"[SKIP] Invalid association row: "
                      f"missing fromObject, toObject, or label -> {association}")
                continue
            self._association_repo.create(association)

    def _import_properties(self) -> None:
        """Import property definitions for each object type."""

        properties_by_object = self._reader.read_properties()
        for object_type, properties in properties_by_object.items():
            self._property_repo.sync(object_type, properties)
