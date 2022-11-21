import requests
import re
import logging
import pandas as pd
import numpy as np
from collections import defaultdict
from utils import request
from tabulate import tabulate
from datetime import (
    date,
    datetime,
    timedelta,
)


class StatusChecker:

    slots_to_check = [
        "lhcb-gauss-dev",
        "lhcb-sim10",
        "lhcb-gaussino",
    ]

    projects_to_check = [
        "Gaudi",
        "Geant4",
        "Detector",
        "Run2Support",
        "GaussinoExtLibs",
        "Gaussino",
        "Gauss",
    ]

    platforms_to_check = [
        "x86_64_v2-centos7-gcc11-opt",
        "x86_64_v2-centos7-gcc11-dbg",
        "x86_64_v2-centos7-gcc11+dd4hep-opt",
    ]

    result_types = {
        "build": {
            "Warnings": "warnings",
            "Errors": "errors",
        },
        "tests": {
            "Passed": "PASS",
            "Failed": "FAIL",
        },
    }

    parsed_result_type = {
        "warnings": "W:",
        "errors": "E:",
        "PASS": "P:",
        "FAIL": "F:",
    }

    hidden_platform_prefix = "x86_64_v2-centos7-gcc11"

    # there is no way you can get the list of build ids
    # from the API, so we have to use the main page...
    main_page = "https://lhcb-nightlies.web.cern.ch/nightly/"

    api_page = "https://lhcb-nightlies.web.cern.ch/api/v1/nightly"

    max_backward_checks = 30

    date_format = "%Y-%m-%d"

    _slots = defaultdict(lambda: 0)

    def __init__(
        self,
        slot_names: list = [],
        platform_names: list = [],
        project_names: list = [],
    ):
        if slot_names:
            self.slots_to_check = slot_names
        if platform_names:
            self.platforms_to_check = platform_names
        if project_names:
            self.projects_to_check = project_names
        self.get_current_builds()

    @request
    def get_current_builds(self):
        logging.debug("Fetching the most recent build ids.")
        response = requests.get(self.main_page)
        response.raise_for_status()
        slots_reg = "|".join(self.slots_to_check)
        slots_reg = rf"(?:{slots_reg})\/[0-9]{{1,4}}\/"
        slot_candidates = re.findall(slots_reg, response.content.decode("utf-8"))
        if not slot_candidates:
            msg = (
                f"No slots from the list '{self.slots_to_check}' "
                f"were found in the content of '{self.main_page}'. "
                "Please, make sure you provided correct slot names."
            )
            logging.error(msg)
            raise ValueError(msg)
        for slot_candidate in slot_candidates:
            slot, build_id, _ = slot_candidate.split("/")
            build_id = int(build_id)
            # pick only the latest builds
            if self._slots[slot] < build_id:
                self._slots[slot] = build_id
        logging.debug(f"Found build ids: {dict(self._slots)}.")

    def _fetch_build_info(
        self,
        slot: str,
        build_id: int,
        parsed_date: str,
    ) -> (pd.DataFrame, str):
        df = pd.DataFrame()
        response = requests.get(f"{self.api_page}/{slot}/{build_id}/summary")
        response.raise_for_status()
        parsed = response.json()
        if parsed["aborted"]:
            return (df, parsed_date)
        for project in parsed["projects"]:
            if project["name"] in self.projects_to_check and project["enabled"]:
                if df.empty:
                    short_platforms = [
                        platform.replace(self.hidden_platform_prefix, "*")
                        for platform in project["results"].keys()
                    ]
                    nested_results_cols = [("Project", ""), ("Failed MRs", "")]
                    nested_results_cols += [
                        (platform, "BUILD / TEST") for platform in short_platforms
                    ]
                    df = pd.DataFrame(
                        columns=pd.MultiIndex.from_tuples(nested_results_cols)
                    )
                ptf_res = []
                for platform, results in project["results"].items():
                    tmp_res = []
                    for check_type, check_values in self.result_types.items():
                        tmp_tmp_res = []
                        for result_type, result_name in check_values.items():
                            try:
                                tmp_tmp_res.append(
                                    f"{self.parsed_result_type[result_name]}"
                                    f"{str(results[check_type][result_name])}"
                                )
                            except TypeError:
                                tmp_tmp_res = ["UNKNOWN"]
                                break
                        tmp_res.append(" ".join(tmp_tmp_res))
                    ptf_res.append(" / ".join(tmp_res))
                failed_MRs = []
                if project["checkout"] and "warnings" in project["checkout"]:
                    for warn in project["checkout"]["warnings"]:
                        tmp_res = re.findall(rf"{project['name']}\![0-9]{{1,5}}", warn)
                        failed_MRs += [r.replace(project["name"], "") for r in tmp_res]
                df.loc[len(df.index)] = [
                    project["name"],
                    ",".join(failed_MRs),
                    *ptf_res,
                ]
        return (df, parsed["date"])

    @request
    def check_status(
        self,
        date_to_check: date = date.today(),
        days: int = 1,
    ):
        msgs = defaultdict(dict)
        for slot, build_id in self._slots.items():
            tmp_build_id = build_id
            for day_delta in range(days):
                date_back = date_to_check - timedelta(days=day_delta)
                parsed_date = date_back.strftime(self.date_format)
                msgs[slot][date_back] = {}
                try:
                    count = 0
                    while True:
                        count += 1
                        if count > self.max_backward_checks:
                            msg = f"Cannot find {slot} for {parsed_date}"
                            logging.error(msg)
                            raise ValueError(msg)
                        df, retrieved_date = self._fetch_build_info(
                            slot,
                            tmp_build_id,
                            parsed_date,
                        )
                        prdate = datetime.strptime(
                            retrieved_date,
                            self.date_format,
                        )
                        if df.empty or prdate > date_back:
                            tmp_build_id -= 1
                            continue
                        elif prdate < date_back:
                            break
                        else:
                            msgs[slot][date_back]["build_id"] = tmp_build_id
                            msgs[slot][date_back]["df"] = df
                            break
                except AttributeError as err:
                    logging.warning(
                        f"Retrieving information for '{slot}/{build_id}' "
                        f" did not work. Error: '{err}'"
                    )
        stream = ""
        for slot, m_values in msgs.items():
            sorted_m_values = dict(sorted(m_values.items(), key=lambda x: x[0]))
            for date_back, values in sorted_m_values.items():
                parsed_date = date_back.strftime(self.date_format)
                if values:
                    stream += f"-> {slot}/{parsed_date}/{values['build_id']}:\n"
                    table = tabulate(
                        values["df"],
                        headers=list(map("\n".join, values["df"].columns.tolist())),
                        tablefmt="pretty",
                    )
                    stream += f"{table}\n"
                else:
                    stream += f"-> {slot}/{parsed_date}: No slot available\n"
        logging.info(stream)

    @request
    def dqcs_report(
        self,
        report_date: date = date.today(),
        days: int = 7,
    ):
        parsed_date = report_date.strftime(self.date_format)
        for slot, build_id in self._slots.items():
            msg = ""
            tmp_build_id = build_id
            try:
                while True:
                    df = self.fetch_build_info(
                        slot,
                        tmp_build_id,
                        parsed_date,
                    )
                    if df.empty:
                        continue
                    msg += f"{slot}/{build_id}:\n"
                    msg += f"{df.to_string()}\n"
                    break
            except AttributeError as err:
                logging.warning(
                    f"Retrieving information for '{slot}/{build_id}' "
                    f" did not work. Error: '{err}'"
                )
                msg += "Something went wrong..."
            logging.info(msg)
