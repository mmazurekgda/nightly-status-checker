import logging
import click
from status_checker import StatusChecker
from datetime import date as dt
from datetime import datetime

try:
    import config as cfg
except ImportError:
    class cfg(object):
        slots_to_check = StatusChecker.slots_to_check
        platforms_to_check = StatusChecker.platforms_to_check
        projects_to_check = StatusChecker.projects_to_check


@click.group()
@click.option("--verbosity", default="INFO", help="verbosity of the logger")
def cli(verbosity):
    root = logging.getLogger()
    root.setLevel(verbosity)


def common(func):
    func = click.option(
        "--date",
        default=dt.today().strftime(StatusChecker.date_format),
        help=f"date of the slot to check (in '{StatusChecker.date_format}')",
    )(func)
    func = click.option(
        "--slots",
        default=cfg.slots_to_check,
        help="list of nightly slot names to check",
        multiple=True,
    )(func)
    func = click.option(
        "--platforms",
        default=cfg.platforms_to_check,
        help="list of platform names to check",
        multiple=True,
    )(func)
    func = click.option(
        "--projects",
        default=cfg.projects_to_check,
        help="list of project names to check",
        multiple=True,
    )(func)
    return func


@click.command()
@common
def current_status(date, slots, platforms, projects):
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


@click.command()
@common
@click.option(
    "--days",
    default=7,
    help="number of days to include in the report",
)
@click.option(
    "--html",
    default=True,
    help="write in HTML format",
)
@click.option(
    "--filepath",
    default="output.html",
    help="path to a file",
)
def dqcs_report(
    date,
    slots,
    platforms,
    projects,
    days,
    html,
    filepath,
):
    """Prepare the DQCS report."""
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
        days=days,
        html=html,
        filepath=filepath,
    )


@click.command()
@common
def mkconfig(date, slots, platforms, projects):
    """Generate config.py to customize
    selection of slots, platforms and projects."""
    cfg_code = """
# Module to customize default configuration of nightly-status-checker

slots_to_check = [
    {slots_list}
]

projects_to_check = [
    {project_list}
]

platforms_to_check = [
    {platform_list}
]
"""
    pretty_sep = ",\n    "
    project_list = []
    platform_list = []
    checker = StatusChecker(
        slot_names=slots,
        platform_names=platforms,
        project_names=projects,
    )
    slots_list = [sn for sn in checker._slots.keys()]
    miss_slots = [sn for sn in StatusChecker.slots_to_check
                  if sn not in slots_list]
    if len(miss_slots) > 0:
        logging.warning("Hardcoded default slots {} not found in Nightly page."
                        " Maybe update package!".format(', '.join(miss_slots)))
    for slot, build in checker._slots.items():
        r = checker._get_Platforms_Projects_for_slot(slot, build)
        project_list += [pn for pn in r[1] if pn not in project_list]
        platform_list += [pn for pn in r[0] if pn not in platform_list]
    slots_str = pretty_sep.join(['"{}"'.format(ss)
                                 for ss in slots_list])
    projects_str = pretty_sep.join(['"{}"'.format(ss)
                                    for ss in project_list])
    platforms_str = pretty_sep.join(['"{}"'.format(ss)
                                     for ss in platform_list])
    with open("config.py", 'w', encoding='utf-8') as fp:
        fp.write(cfg_code.format(slots_list=slots_str,
                                 project_list=projects_str,
                                 platform_list=platforms_str))
        fp.flush()
    logging.info("'config.py' file written to disk. "
                 "Edit accordingly and run script again for desired function.")


cli.add_command(current_status)
cli.add_command(dqcs_report)
cli.add_command(mkconfig)

if __name__ == "__main__":
    cli()
