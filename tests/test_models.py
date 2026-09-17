"""Tests for domain models: row parsing, defaults, and payload shaping."""
from src.domain.models import AssociationDefinition, ObjectSchemaDefinition, PropertyDefinition

# pylint: disable=missing-function-docstring
class TestObjectSchemaDefinition:
    """Tests for ObjectSchemaDefinition.from_row / to_payload."""

    def test_from_row_applies_defaults(self):
        definition = ObjectSchemaDefinition.from_row({"name": "car"})

        assert definition.singular_label == "Car"
        assert definition.plural_label == "Cars"
        assert definition.primary_display_property == "car_name"
        assert definition.primary_display_label == "Car Name"
        assert definition.required_properties == ["car_name"]
        assert definition.searchable_properties == ["car_name"]
        assert definition.associated_objects == ["CONTACT", "COMPANY"]

    def test_from_row_uses_provided_values(self):
        row = {
            "name": "car",
            "singularLabel": "Vehicle",
            "pluralLabel": "Vehicles",
            "primaryDisplayProperty": "vin",
            "requiredProperties": "vin, make",
            "associatedObjects": "deal",
        }
        definition = ObjectSchemaDefinition.from_row(row)

        assert definition.singular_label == "Vehicle"
        assert definition.required_properties == ["vin", "make"]
        assert definition.associated_objects == ["DEAL"]

    def test_to_payload_shape(self):
        definition = ObjectSchemaDefinition.from_row({"name": "car"})
        payload = definition.to_payload()

        assert payload["name"] == "car"
        assert payload["labels"] == {"singular": "Car", "plural": "Cars"}
        assert payload["properties"][0]["name"] == "car_name"


class TestAssociationDefinition:
    """Tests for AssociationDefinition.from_row / is_valid."""

    def test_is_valid_true_when_required_fields_present(self):
        definition = AssociationDefinition.from_row(
            {"fromObject": "contacts", "toObject": "companies", "label": "Employee"}
        )

        assert definition.is_valid
        assert definition.inverse_label == "Employee"
        assert definition.name == "employee"

    def test_is_valid_false_when_missing_label(self):
        definition = AssociationDefinition.from_row(
            {"fromObject": "contacts", "toObject": "companies", "label": ""}
        )

        assert not definition.is_valid


class TestPropertyDefinition:
    """Tests for PropertyDefinition.from_row / options parsing."""

    def test_default_group_for_contacts(self):
        definition = PropertyDefinition.from_row("contacts", {"name": "favorite_color"})

        assert definition.group_name == "contactinformation"
        assert definition.type == "string"
        assert definition.field_type == "text"

    def test_default_group_for_other_objects(self):
        definition = PropertyDefinition.from_row("cars", {"name": "vin"})

        assert definition.group_name == "custom_properties"

    def test_options_parsing_with_labels_and_values(self):
        row = {"name": "color", "options": "Red:red, Blue:blue"}
        definition = PropertyDefinition.from_row("cars", row)

        assert definition.options == [
            {"label": "Red", "value": "red", "displayOrder": 0},
            {"label": "Blue", "value": "blue", "displayOrder": 1},
        ]

    def test_options_parsing_without_explicit_values(self):
        row = {"name": "color", "options": "Red, Blue"}
        definition = PropertyDefinition.from_row("cars", row)

        assert definition.options == [
            {"label": "Red", "value": "red", "displayOrder": 0},
            {"label": "Blue", "value": "blue", "displayOrder": 1},
        ]

    def test_to_payload_omits_options_when_none(self):
        definition = PropertyDefinition.from_row("cars", {"name": "vin"})

        assert "options" not in definition.to_payload()
