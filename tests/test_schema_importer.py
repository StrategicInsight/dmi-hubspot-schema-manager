"""Tests for SchemaImporter orchestration using fake reader/repositories."""
from typing import cast

from hubspot_schema_manager.application.schema_importer import SchemaImporter
from hubspot_schema_manager.domain.models import (
    AssociationDefinition,
    ObjectSchemaDefinition,
    PropertyDefinition,
)
from hubspot_schema_manager.infrastructure.repositories import (
    AssociationRepository,
    PropertyRepository,
    SchemaRepository,
)


# pylint: disable=missing-function-docstring
class FakeReader:
    """Fake SourceReader returning canned definitions."""

    def __init__(self, objects=None, associations=None, properties=None):
        self._objects = objects or []
        self._associations = associations or []
        self._properties = properties or {}

    def read_objects(self):
        return self._objects

    def read_associations(self):
        return self._associations

    def read_properties(self):
        return self._properties


class FakeSchemaRepo:
    """Fake SchemaRepository recording calls."""

    def __init__(self, existing=None):
        self._existing = existing or {}
        self.created = []

    def get_existing(self):
        return self._existing

    def create(self, schema, existing):
        self.created.append((schema, existing))


class FakeAssociationRepo:
    """Fake AssociationRepository recording calls."""

    def __init__(self):
        self.created = []

    def create(self, association):
        self.created.append(association)


class FakePropertyRepo:
    """Fake PropertyRepository recording calls."""

    def __init__(self):
        self.synced = []

    def sync(self, object_type, properties):
        self.synced.append((object_type, properties))


def make_importer(reader, schema_repo=None, association_repo=None, property_repo=None):
    return SchemaImporter(
        reader=reader,
        schema_repo=cast(SchemaRepository, schema_repo or FakeSchemaRepo()),
        association_repo=cast(AssociationRepository, association_repo or FakeAssociationRepo()),
        property_repo=cast(PropertyRepository, property_repo or FakePropertyRepo()),
    )


def test_run_creates_object_schemas():
    schema = ObjectSchemaDefinition.from_row({"name": "car"})
    schema_repo = FakeSchemaRepo(existing={"foo": {}})
    reader = FakeReader(objects=[schema])

    make_importer(reader, schema_repo=schema_repo).run()

    assert schema_repo.created == [(schema, {"foo": {}})]


def test_run_skips_object_import_when_none_found():
    schema_repo = FakeSchemaRepo()
    reader = FakeReader(objects=[])

    make_importer(reader, schema_repo=schema_repo).run()

    assert not schema_repo.created


def test_run_creates_valid_associations_and_skips_invalid():
    valid = AssociationDefinition.from_row(
        {"fromObject": "contacts", "toObject": "companies", "label": "Employee"}
    )
    invalid = AssociationDefinition.from_row({"fromObject": "", "toObject": "", "label": ""})
    association_repo = FakeAssociationRepo()
    reader = FakeReader(associations=[valid, invalid])

    make_importer(reader, association_repo=association_repo).run()

    assert association_repo.created == [valid]


def test_run_syncs_properties_by_object():
    prop = PropertyDefinition.from_row("cars", {"name": "vin"})
    property_repo = FakePropertyRepo()
    reader = FakeReader(properties={"cars": [prop]})

    make_importer(reader, property_repo=property_repo).run()

    assert property_repo.synced == [("cars", [prop])]
