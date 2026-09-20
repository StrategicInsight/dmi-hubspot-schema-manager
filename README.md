# dmi-hubspot-schema-manager

CLI for importing HubSpot schema metadata from spreadsheet files.

It syncs three resource types into HubSpot:

- Custom object schemas
- Association labels
- Object properties

## Requirements

- Python 3.14+
- A HubSpot private app token for live runs

## Local Development Setup

From the repository root:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Smoke test the installed CLI:

```powershell
hubspot-schema-manager --help
```

If you do not want an editable install, use `python -m pip install .` instead.

## Environment Configuration

The app loads configuration from either:

- Environment variables in the current shell
- A `.env` file in the current working directory

Supported settings:

- `HUBSPOT_ACCESS_TOKEN`: required for live execution
- `BASE_URL`: optional, defaults to `https://api.hubapi.com`
- `RATE_LIMIT_DELAY`: optional, defaults to `0.15`

If you use `--dry-run`, `HUBSPOT_ACCESS_TOKEN` is not required.

Example `.env`:

```env
HUBSPOT_ACCESS_TOKEN=your-token
BASE_URL=https://api.hubapi.com
RATE_LIMIT_DELAY=0.15
```

## Run Locally

After activating the virtual environment and installing the package:

```powershell
hubspot-schema-manager data\schema.xlsx --dry-run
hubspot-schema-manager data\schema.xlsx
```

Module form also works after install:

```powershell
python -m hubspot_schema_manager.cli data\schema.xlsx --dry-run
```

## Build Distributable Artifacts

Build a wheel and source distribution from the repository root:

```powershell
python -m pip install build
python -m build
```

Artifacts are written to `dist/`:

- `dist\dmi_hubspot_schema_manager-<version>-py3-none-any.whl`
- `dist\dmi_hubspot_schema_manager-<version>.tar.gz`

## Install From a Downloaded Artifact

If another developer downloads a built package from the repository or CI artifacts, they can install it without cloning the repo.

Example using a wheel:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install .\dmi_hubspot_schema_manager-0.1.0-py3-none-any.whl
```

Example using a source distribution:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install .\dmi_hubspot_schema_manager-0.1.0.tar.gz
```

Then configure the environment in one of these ways:

- Set `HUBSPOT_ACCESS_TOKEN`, `BASE_URL`, and `RATE_LIMIT_DELAY` in the shell
- Create a `.env` file in the folder where you run `hubspot-schema-manager`

Run the installed CLI against any spreadsheet path you can access:

```powershell
hubspot-schema-manager .\schema.xlsx --dry-run
```

## Supported Input Behavior

### Excel

Excel files support all three import types.

Recognized worksheet names:

- Objects: `objects`, `schemas`, `custom_objects`
- Associations: `associations`, `association_labels`, `labels`
- Properties: `properties`, `fields`, `attributes`

If no property sheet matches, the importer falls back to the first worksheet.

## Schema Template

The repository includes a sample workbook at `data\schema_definitions.xlsx` with three sheets:

- `Objects`
- `Properties`
- `Associations`

The code that reads the workbook lives in `src/hubspot_schema_manager/infrastructure/readers.py`, and the row-to-model mapping lives in `src/hubspot_schema_manager/domain/models.py`.

### Objects Sheet

Columns:

- `name`: Internal HubSpot object name. This should be lowercase and API-safe, for example `asset`.
- `singularLabel`: Singular UI label shown in HubSpot, for example `Asset`.
- `pluralLabel`: Plural UI label shown in HubSpot, for example `Assets`.
- `primaryDisplayProperty`: Internal name of the main text property used to represent the record.
- `primaryDisplayLabel`: UI label for the primary display property.
- `associatedObjects`: Comma-separated list of objects this custom object can associate with when the schema is created.

Sample row:

| name | singularLabel | pluralLabel | primaryDisplayProperty | primaryDisplayLabel | associatedObjects |
| --- | --- | --- | --- | --- | --- |
| asset | Asset | Assets | fum_record_type | FUM Record Type | CONTACT,COMPANY,PRODUCT |

Notes:

- If `singularLabel` is blank, the code defaults to a capitalized form of `name`.
- If `pluralLabel` is blank, the code defaults to the capitalized name plus `s`.
- If `primaryDisplayProperty` is blank, the code defaults to `<name>_name`.
- If `primaryDisplayLabel` is blank, the code defaults to `<Name> Name`.
- The object model also supports `requiredProperties` and `searchableProperties`, but those columns are not present in the shipped workbook template. When omitted, both default to the primary display property.
- If `associatedObjects` is blank, the code defaults to `CONTACT,COMPANY`.

### Properties Sheet

Columns:

- `object`: The target object type for the property, for example `contacts`, `companies`, or a custom object such as `asset`.
- `name`: Internal HubSpot property name.
- `label`: UI label shown in HubSpot.
- `type`: HubSpot storage type, such as `string`, `number`, `date`, `datetime`, `bool`, or `enumeration`.
- `fieldType`: HubSpot field control type, such as `text`, `textarea`, `select`, `radio`, `checkbox`, or `date`.
- `groupName`: HubSpot property group name.
- `options`: Comma-separated option values for enumerated fields. You can use either `Label` or `Label:value` format.
- `unique`: Whether HubSpot should enforce unique values for this property.

Sample rows:

| object | name | label | type | fieldType | groupName | options | unique |
| --- | --- | --- | --- | --- | --- | --- | --- |
| contacts | contact_record_type | Contact Record Type | string | text | contactinformation |  | false |
| asset | asset_status | Asset Status | enumeration | select | custom_properties | Active:active, Inactive:inactive | false |

Notes:

- If `label` is blank, the code defaults it to the property `name`.
- If `type` is blank, the code defaults to `string`.
- If `fieldType` is blank, the code defaults to `text`.
- If `groupName` is blank, the code defaults to `contactinformation` for `contacts` and `custom_properties` for every other object type.
- `unique` is treated as true only when the value is `true`, `1`, or `yes`.
- For `options`, `Red, Blue` becomes `red` and `blue` internally, while `Red:red, Blue:blue` preserves the explicit values.

### Associations Sheet

Columns:

- `fromObject`: The source object type.
- `toObject`: The target object type.
- `label`: The forward label shown from the `fromObject` side.
- `inverseLabel`: The reverse label shown from the `toObject` side.
- `name`: Internal association definition name.

Sample rows:

| fromObject | toObject | label | inverseLabel | name |
| --- | --- | --- | --- | --- |
| contacts | companies | Account | Contacts | account_contact |
| asset | contacts | FUM Contact | Financial Feeds | fum_contact |
| companies | companies | Umbrella Account | Child Accounts | umbrella_account |

How to read them:

- `contacts -> companies` with `Account / Contacts` means a contact points to a company as its `Account`, and the company sees those related contacts as `Contacts`.
- `asset -> contacts` with `FUM Contact / Financial Feeds` means an asset points to a contact as its `FUM Contact`, and the contact sees those related assets as `Financial Feeds`.
- `companies -> companies` with `Umbrella Account / Child Accounts` is a self-association where one company is the parent-side account and the other is the child-side account.

Notes:

- `fromObject`, `toObject`, and `label` are required for a valid row.
- If `inverseLabel` is blank, the code defaults it to the same value as `label`.
- If `name` is blank, the code defaults it to a lowercase underscore version of `label`.

### Association Cardinality

This workbook does not define hard cardinality such as one-to-one, one-to-many, or many-to-many.

What this importer creates is the association label definition only. The payload sent by the code contains:

- `label`
- `inverseLabel`
- `name`

That means:

- You cannot determine cardinality from the template alone.
- The README examples on the `Associations` sheet describe relationship meaning, not relationship count limits.
- Custom association rows should be treated as label definitions, not as enforcement rules.

In practice, cardinality is determined outside this workbook flow:

- By HubSpot built-in association behavior for certain default association types
- By HubSpot association limits or settings configured separately
- By your application logic if you choose to enforce stricter rules yourself

Example:

- `contacts -> companies` with label `Account` does not mean one contact can only ever have one account. It only defines the label unless HubSpot or external logic enforces a stricter rule.

### CSV

CSV handling is intentionally simple:

- If the file contains `fromObject` and `toObject`, it is treated as association data.
- Otherwise, if it contains an `object` column, it is treated as property data grouped by object type.
- Object schema import from CSV is not implemented.

## Import Flow

`SchemaImporter.run()` performs work in this order:

1. Import object schemas
2. Import association labels
3. Import properties

Repositories avoid duplicate creation by checking existing HubSpot resources first.

## Tests

Run the test suite from the repository root:

```powershell
python -m pytest
```

`pytest.ini` configures the `src` layout for test runs.

## Code Layout

```text
src/
	hubspot_schema_manager/
		application/
			schema_importer.py
		domain/
			models.py
		infrastructure/
			hubspot_client.py
			readers.py
			repositories.py
		cli.py
		config.py

tests/
	test_models.py
	test_repositories.py
	test_schema_importer.py
```
