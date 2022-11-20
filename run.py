import logging
import click
from status_checker import StatusChecker
from datetime import date as dt
from datetime import datetime


@click.group()
@click.option("--verbosity", default="INFO", help="verbosity of the logger")
def cli(verbosity):
    root = logging.getLogger()
    root.setLevel(verbosity)


@click.command()
@click.option(
    "--date",
    default=dt.today().strftime(StatusChecker.date_format),
    help=f"date of the slot to check (in '{StatusChecker.date_format}')",
)
@click.option(
    "--slots",
    default=StatusChecker.slots_to_check,
    help="list of nightly slot names to check",
    multiple=True,
)
@click.option(
    "--platforms",
    default=StatusChecker.platforms_to_check,
    help="list of platform names to check",
    multiple=True,
)
@click.option(
    "--projects",
    default=StatusChecker.projects_to_check,
    help="list of project names to check",
    multiple=True,
)
def check_status(date, slots, platforms, projects):
    """Print in the terminal the summary of nightly slots"""
    checker = StatusChecker(
        slot_names=slots,
        platform_names=platforms,
        project_names=projects,
    )
    checker.check_status(
        date_to_check=datetime.strptime(
            date,
            StatusChecker.date_format,
        ),
    )


cli.add_command(check_status)

if __name__ == "__main__":
    cli()
