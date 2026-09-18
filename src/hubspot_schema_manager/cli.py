"""CLI composition root: wires config, HTTP client, readers, and repositories together."""
import argparse
import sys
from pathlib import Path

from .application.schema_importer import SchemaImporter
from .config import Settings
from .infrastructure.hubspot_client import HubSpotClient
from .infrastructure.readers import create_reader
from .infrastructure.repositories import (
    AssociationRepository,
    PropertyRepository,
    SchemaRepository,
)

SECTION_SEPARATOR = "=" * 70

def build_importer(file_path: Path, dry_run: bool) -> SchemaImporter:
    """Builds SchemaImporter class"""

    settings = Settings()
    if not settings.hubspot_access_token and not dry_run:
        print("[ERROR] HUBSPOT_ACCESS_TOKEN environment variable is not set. Exiting.")
        sys.exit(1)

    client = HubSpotClient(
        base_url=settings.base_url,
        token=settings.hubspot_access_token or "dummy_token",
        rate_limit_delay=settings.rate_limit_delay,
    )
    reader = create_reader(file_path)
    return SchemaImporter(
        reader=reader,
        schema_repo=SchemaRepository(client, dry_run=dry_run),
        association_repo=AssociationRepository(client, dry_run=dry_run),
        property_repo=PropertyRepository(client, dry_run=dry_run),
    )


def main() -> None:
    """Main orchestrator of schema manager"""

    parser = argparse.ArgumentParser(
        description="Import HubSpot Schemas, Association Labels, and Properties from Excel/CSV."
    )
    parser.add_argument("file", help="Path to .xlsx, .xls or .csv file")
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Perform a dry run without modifying CRM schema"
    )
    args = parser.parse_args()

    file_path = Path(args.file)
    print(SECTION_SEPARATOR)
    print(" HubSpot Schema & Association Importer")
    print(f" Source File : {file_path}")
    print(f" Mode        : "
          f"{'DRY RUN (No changes will be written)' if args.dry_run else 'LIVE EXECUTION'}"
    )
    print(SECTION_SEPARATOR)

    build_importer(file_path, args.dry_run).run()

    print("\n" + SECTION_SEPARATOR)
    print(" Import process finished successfully!")
    print(SECTION_SEPARATOR)


if __name__ == "__main__":
    raise SystemExit(main())
