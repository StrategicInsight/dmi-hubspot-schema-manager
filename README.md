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
