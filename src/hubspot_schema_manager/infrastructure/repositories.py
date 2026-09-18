"""Repositories: one class per HubSpot resource type, each with a single responsibility."""
from hubspot_schema_manager.infrastructure.hubspot_client import HttpClient
from hubspot_schema_manager.domain.models import (
    AssociationDefinition,
    ObjectSchemaDefinition,
    PropertyDefinition
)


class SchemaRepository:
    """Manage HubSpot object schemas through the API."""

    def __init__(self, client: HttpClient, dry_run: bool = False):
        """Initialize the repository with an HTTP client."""

        self._client = client
        self._dry_run = dry_run

    def get_existing(self) -> dict[str, dict]:
        """Fetch all existing CRM object schemas, keyed by name and fully qualified name."""

        response = self._client.get("/crm/v3/schemas")
        if not response.ok:
            print(f"[ERROR] Failed to fetch schemas: {response.status_code} - {response.text}")
            return {}

        schemas: dict[str, dict] = {}
        for item in response.data.get("results", []):
            schemas[item["name"]] = item
            if "fullyQualifiedName" in item:
                schemas[item["fullyQualifiedName"]] = item
        return schemas

    def create(self, schema: ObjectSchemaDefinition, existing: dict[str, dict]) -> None:
        """Create an object schema if it does not already exist."""

        if schema.name in existing:
            print(f"[SKIP] Custom object '{schema.name}' already exists.")
            return

        print(f"\n--- [CREATING OBJECT SCHEMA] {schema.name} ---")
        payload = schema.to_payload()
        if self._dry_run:
            print(f"[DRY-RUN] Would create schema for '{schema.name}' with payload:\n{payload}")
            return

        response = self._client.post("/crm/v3/schemas", payload)
        if response.ok:
            fqn = response.data.get("fullyQualifiedName", response.data.get("id"))
            print(f"[SUCCESS] Custom object '{schema.name}' "
                  f"created successfully! (ID / FQN: {fqn})")
        else:
            print(f"[ERROR] Failed creating object '{schema.name}': "
                  f"{response.status_code} - {response.text}")


class AssociationRepository:
    """Manage HubSpot association labels through the API."""

    def __init__(self, client: HttpClient, dry_run: bool = False):
        """Initialize the repository with an HTTP client."""

        self._client = client
        self._dry_run = dry_run

    def get_existing_labels(self, from_object: str, to_object: str) -> set[str]:
        """Fetch existing labels between two object types."""

        response = self._client.get(f"/crm/v4/associations/{from_object}/{to_object}/labels")
        if not response.ok:
            return set()

        labels: set[str] = set()
        for item in response.data.get("results", []):
            if item.get("label"):
                labels.add(item["label"].strip().lower())
            if item.get("inverseLabel"):
                labels.add(item["inverseLabel"].strip().lower())
        return labels

    def create(self, association: AssociationDefinition) -> None:
        """Create an association label if it does not exist."""

        print(f"\n--- [ASSOCIATION LABEL] {association.from_object} <-> "
              f"{association.to_object} ('{association.label}') ---")

        existing_labels = self.get_existing_labels(association.from_object, association.to_object)
        if association.label.lower() in existing_labels:
            print(f"[SKIP] Association label '{association.label}' already exists "
                  f"between {association.from_object} and {association.to_object}.")
            return

        payload = association.to_payload()
        path = f"/crm/v4/associations/{association.from_object}/{association.to_object}/labels"
        if self._dry_run:
            print(f"[DRY-RUN] Would create association label on {path}:\n{payload}")
            return

        response = self._client.post(path, payload)
        if response.ok:
            print(f"[SUCCESS] Association label '{association.label}' created "
                  f"between {association.from_object} and {association.to_object}.")
        else:
            print(f"[ERROR] Failed to create association label '{association.label}': "
                  f"{response.status_code} - {response.text}")


class PropertyRepository:
    """Manage HubSpot object properties through the API."""

    def __init__(self, client: HttpClient, dry_run: bool = False):
        """Initialize the repository with an HTTP client."""

        self._client = client
        self._dry_run = dry_run

    def get_existing(self, object_type: str) -> set[str]:
        """Fetch existing property names for an object type."""

        response = self._client.get(f"/crm/v3/properties/{object_type}")
        if not response.ok:
            print(f"[WARN] Could not fetch properties for '{object_type}': "
                  f"{response.status_code} - {response.text}")
            return set()
        return {item["name"] for item in response.data.get("results", [])}

    def sync(self, object_type: str, properties: list[PropertyDefinition]) -> None:
        """Create properties that do not already exist."""

        print(f"\n--- [SYNC PROPERTIES] {object_type} ({len(properties)} fields) ---")
        existing_names = self.get_existing(object_type)

        for prop in properties:
            if not prop.name:
                continue
            if prop.name in existing_names:
                print(f"[SKIP] Property '{prop.name}' already exists on {object_type}.")
                continue

            payload = prop.to_payload()
            if self._dry_run:
                print(f"[DRY-RUN] Would create property '{prop.name}' on {object_type}:\n{payload}")
                continue

            response = self._client.post(f"/crm/v3/properties/{object_type}", payload)
            if response.ok:
                print(f"[SUCCESS] Property '{prop.name}' created on {object_type}.")
                existing_names.add(prop.name)
            else:
                print(f"[ERROR] Failed to create property '{prop.name}' "
                      f"on {object_type}: {response.status_code} - {response.text}")
