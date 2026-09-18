"""Domain models for the three importable HubSpot resource types."""
import math
from dataclasses import dataclass


def _trim(value: object, default: str = "") -> str:
    """Return a stripped string, falling back to `default` for missing/NaN values."""

    if value is None:
        return default
    if isinstance(value, float) and math.isnan(value):  # NaN check without a pandas dependency
        return default
    text = str(value).strip()
    return text if text else default


def _split_csv(value: object, default: str = "") -> list[str]:
    """Split ttrimmed string into comma-delimited string"""

    return [p.strip() for p in _trim(value, default).split(",") if p.strip()]


@dataclass
class ObjectSchemaDefinition:
    """Represents a HubSpot custom object schema definition."""

    name: str
    singular_label: str
    plural_label: str
    primary_display_property: str
    primary_display_label: str
    required_properties: list[str]
    searchable_properties: list[str]
    associated_objects: list[str]

    @classmethod
    def from_row(cls, row: dict) -> "ObjectSchemaDefinition":
        """Create an object schema definition from a spreadsheet row."""

        name = _trim(row.get("name"))
        primary_display_property = _trim(row.get("primaryDisplayProperty"), f"{name}_name")
        return cls(
            name=name,
            singular_label=_trim(row.get("singularLabel"), name.capitalize()),
            plural_label=_trim(row.get("pluralLabel"), f"{name.capitalize()}s"),
            primary_display_property=primary_display_property,
            primary_display_label=_trim(
                row.get("primaryDisplayLabel"),
                f"{name.capitalize()} Name"
            ),
            required_properties=_split_csv(
                row.get("requiredProperties"),
                primary_display_property
            ),
            searchable_properties=_split_csv(
                row.get("searchableProperties"),
                primary_display_property
            ),
            associated_objects=[
                obj.upper()
                for obj in _split_csv(
                    row.get("associatedObjects"),
                    "CONTACT,COMPANY",
                )
            ],
        )

    def to_payload(self) -> dict:
        """Convert the schema definition into a HubSpot API payload."""

        return {
            "name": self.name,
            "labels": {"singular": self.singular_label, "plural": self.plural_label},
            "primaryDisplayProperty": self.primary_display_property,
            "requiredProperties": self.required_properties,
            "searchableProperties": self.searchable_properties,
            "properties": [
                {
                    "name": self.primary_display_property,
                    "label": self.primary_display_label,
                    "type": "string",
                    "fieldType": "text",
                }
            ],
            "associatedObjects": self.associated_objects,
        }


@dataclass
class AssociationDefinition:
    """Represents a HubSpot object association."""

    from_object: str
    to_object: str
    label: str
    inverse_label: str
    name: str

    @classmethod
    def from_row(cls, row: dict) -> "AssociationDefinition":
        """Create an association definition from a spreadsheet row."""

        from_object = _trim(row.get("fromObject"))
        to_object = _trim(row.get("toObject"))
        label = _trim(row.get("label"))
        return cls(
            from_object=from_object,
            to_object=to_object,
            label=label,
            inverse_label=_trim(row.get("inverseLabel"), label),
            name=_trim(row.get("name"), label.lower().replace(" ", "_")),
        )

    @property
    def is_valid(self) -> bool:
        """Return True when the association definition is valid."""

        return bool(self.from_object and self.to_object and self.label)

    def to_payload(self) -> dict:
        """
        Convert the association definition into a HubSpot API payload.

        Returns Dictionary formatted for HubSpot association creation.
        """
        return {"label": self.label, "inverseLabel": self.inverse_label, "name": self.name}


@dataclass
class PropertyDefinition:
    """Represents a HubSpot property definition."""

    object_type: str
    name: str
    label: str
    type: str
    field_type: str
    group_name: str
    has_unique_value: bool
    options: list[dict] | None

    @classmethod
    def from_row(cls, object_type: str, row: dict) -> "PropertyDefinition":
        """Create a property definition from a spreadsheet row."""

        name = _trim(row.get("name"))
        if object_type.lower() == "contacts":
            default_group = "contactinformation"
        else:
            default_group = "custom_properties"
        return cls(
            object_type=object_type,
            name=name,
            label=_trim(row.get("label"), name),
            type=_trim(row.get("type"), "string").lower(),
            field_type=_trim(row.get("fieldType"), "text").lower(),
            group_name=_trim(row.get("groupName"), default_group),
            has_unique_value=_trim(row.get("unique"), "false").lower() in ("true", "1", "yes"),
            options=cls._parse_options(row.get("options")),
        )

    @staticmethod
    def _parse_options(raw_options: object) -> list[dict] | None:
        """Convert raw option text into HubSpot property options."""

        text = _trim(raw_options)
        if not text:
            return None

        options = []
        for index, token in enumerate(t.strip() for t in text.split(",") if t.strip()):
            if ":" in token:
                label, value = token.split(":", 1)
                options.append(
                    {
                        "label": label.strip(), 
                        "value": value.strip(), 
                        "displayOrder": index
                    }
                )
            else:
                options.append(
                    {
                        "label": token, 
                        "value": token.lower().replace(" ", "_"), 
                        "displayOrder": index
                    }
                )
        return options

    def to_payload(self) -> dict:
        """Convert the property definition into a HubSpot API payload."""

        payload = {
            "name": self.name,
            "label": self.label,
            "type": self.type,
            "fieldType": self.field_type,
            "groupName": self.group_name,
            "hasUniqueValue": self.has_unique_value,
        }
        if self.options:
            payload["options"] = self.options
        return payload
