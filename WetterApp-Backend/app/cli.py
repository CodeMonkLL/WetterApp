import click
from flask import Flask

from app.Service.download_data import DEFAULT_WORKERS, import_all_stations


def register_cli(app: Flask) -> None:
    @app.cli.command("import-dwd")
    @click.option("--workers", default=DEFAULT_WORKERS, show_default=True, help="Anzahl paralleler Downloads.")
    @click.option("--limit", type=int, default=None, help="Nur die ersten N Stationen importieren (zum Testen).")
    def import_dwd(workers: int, limit: int | None) -> None:
        """Lädt die DWD-Tageswerte und schreibt sie in die Datenbank."""
        results = import_all_stations(workers=workers, limit=limit)

        imported = sum(int(result["imported"]) for result in results)
        problems = [result for result in results if result["status"] != "imported"]

        click.echo(f"{len(results)} Stationen verarbeitet, {imported} Tageswerte geschrieben.")
        for problem in problems:
            click.echo(f"  {problem['station_id']}: {problem['status']} - {problem['message']}")
