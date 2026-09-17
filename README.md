# dmi-hubspot-schema-manager

Small CLI for importing HubSpot schema metadata from spreadsheet files.

It can sync three resource types into HubSpot:

- Custom object schemas
- Association labels
- Object properties

## What Is In The Codebase

The code is organized into three simple layers:

- `src/application/`: orchestration logic. `SchemaImporter` coordinates the import flow.
- `src/domain/`: data models and payload-building logic for objects, associations, and properties.
- `src/infrastructure/`: file readers and HubSpot API access.

Main entry point:

- `src/cli.py`: parses CLI arguments, loads settings, builds dependencies, and runs the importer.

## Requirements

- Python 3.11+
- HubSpot private app token for live runs

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Configuration is loaded from environment variables or a local `.env` file.

Supported settings:

- `HUBSPOT_ACCESS_TOKEN`: required for live execution
- `BASE_URL`: optional, defaults to `https://api.hubapi.com`
- `RATE_LIMIT_DELAY`: optional, defaults to `0.15`

If `--dry-run` is used, `HUBSPOT_ACCESS_TOKEN` is not required.

Example `.env`:

```env
HUBSPOT_ACCESS_TOKEN=your-token
BASE_URL=https://api.hubapi.com
RATE_LIMIT_DELAY=0.15
```

## Usage

Run the CLI as a module from the repository root:

```bash
python -m src.cli <file>
python -m src.cli <file> --dry-run
```

Example:

```bash
python -m src.cli data/schema.xlsx --dry-run
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

The project includes `pytest` tests for:

- Domain model parsing and payload generation
- Import orchestration
- HubSpot repositories with fake HTTP clients

Run tests:

```bash
python -m pytest
```

`pytest.ini` is configured to use the `src` layout during test runs.

## Project Structure

```text
src/
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