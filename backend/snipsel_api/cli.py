from __future__ import annotations

from flask.cli import FlaskGroup

from snipsel_api.app import create_app
from snipsel_api.commands import cleanup, db_init, process_reminders_command


def _create_app():
    return create_app()


cli = FlaskGroup(create_app=_create_app)
cli.add_command(db_init)
cli.add_command(cleanup)
cli.add_command(process_reminders_command, "process-reminders")

if __name__ == "__main__":
    cli()
