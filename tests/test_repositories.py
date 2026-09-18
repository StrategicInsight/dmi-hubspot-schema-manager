"""Tests for HubSpot repositories using a fake HttpClient (no real network calls)."""
from hubspot_schema_manager.infrastructure.hubspot_client import HubSpotResponse
from hubspot_schema_manager.infrastructure.repositories import (
    AssociationRepository,
    PropertyRepository,
    SchemaRepository,
)
from hubspot_schema_manager.domain.models import (
    AssociationDefinition,
    ObjectSchemaDefinition,
    PropertyDefinition
)

# pylint: disable=missing-function-docstring
class FakeHttpClient:
    """Fake HttpClient returning queued responses and recording requests made."""

    def __init__(self):
        self.get_responses = {}
        self.post_response = HubSpotResponse(status_code=201, data={}, text="")
        self.posts = []

    def get(self, path):
        return self.get_responses.get(path, HubSpotResponse(status_code=200, data={}, text=""))

    def post(self, path, payload):
        self.posts.append((path, payload))
        return self.post_response


class TestSchemaRepository:
    """Tests for SchemaRepository."""

    def test_get_existing_indexes_by_name_and_fqn(self):
        client = FakeHttpClient()
        client.get_responses["/crm/v3/schemas"] = HubSpotResponse(
            status_code=200,
            data={"results": [{"name": "car", "fullyQualifiedName": "p123_car"}]},
            text="",
        )
        repo = SchemaRepository(client)

        existing = repo.get_existing()

        assert existing["car"]["fullyQualifiedName"] == "p123_car"
        assert existing["p123_car"] is existing["car"]

    def test_create_skips_when_already_exists(self):
        client = FakeHttpClient()
        repo = SchemaRepository(client)
        schema = ObjectSchemaDefinition.from_row({"name": "car"})

        repo.create(schema, existing={"car": {}})

        assert client.posts == []

    def test_create_posts_payload_when_missing(self):
        client = FakeHttpClient()
        repo = SchemaRepository(client)
        schema = ObjectSchemaDefinition.from_row({"name": "car"})

        repo.create(schema, existing={})

        assert client.posts == [("/crm/v3/schemas", schema.to_payload())]

    def test_create_dry_run_does_not_post(self):
        client = FakeHttpClient()
        repo = SchemaRepository(client, dry_run=True)
        schema = ObjectSchemaDefinition.from_row({"name": "car"})

        repo.create(schema, existing={})

        assert client.posts == []


class TestAssociationRepository:
    """Tests for AssociationRepository."""

    def test_create_skips_when_label_exists(self):
        client = FakeHttpClient()
        client.get_responses["/crm/v4/associations/contacts/companies/labels"] = HubSpotResponse(
            status_code=200,
            data={"results": [{"label": "Employee"}]},
            text="",
        )
        repo = AssociationRepository(client)
        association = AssociationDefinition.from_row(
            {"fromObject": "contacts", "toObject": "companies", "label": "Employee"}
        )

        repo.create(association)

        assert client.posts == []

    def test_create_posts_when_label_missing(self):
        client = FakeHttpClient()
        repo = AssociationRepository(client)
        association = AssociationDefinition.from_row(
            {"fromObject": "contacts", "toObject": "companies", "label": "Employee"}
        )

        repo.create(association)

        assert client.posts == [
            ("/crm/v4/associations/contacts/companies/labels", association.to_payload())
        ]


class TestPropertyRepository:
    """Tests for PropertyRepository."""

    def test_sync_skips_existing_and_creates_missing(self):
        client = FakeHttpClient()
        client.get_responses["/crm/v3/properties/cars"] = HubSpotResponse(
            status_code=200,
            data={"results": [{"name": "vin"}]},
            text="",
        )
        repo = PropertyRepository(client)
        existing_prop = PropertyDefinition.from_row("cars", {"name": "vin"})
        new_prop = PropertyDefinition.from_row("cars", {"name": "color"})

        repo.sync("cars", [existing_prop, new_prop])

        assert client.posts == [("/crm/v3/properties/cars", new_prop.to_payload())]

    def test_sync_dry_run_does_not_post(self):
        client = FakeHttpClient()
        repo = PropertyRepository(client, dry_run=True)
        new_prop = PropertyDefinition.from_row("cars", {"name": "color"})

        repo.sync("cars", [new_prop])

        assert client.posts == []
