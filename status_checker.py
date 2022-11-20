import requests
import re
import logging
import pandas as pd
import numpy as np
from collections import defaultdict
from utils import request
from datetime import (
    date,
    datetime,
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

    _all_result_types = {
        **result_types["build"],
        **result_types["tests"],
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
                    nested_results_cols = [("Project", "")]
                    nested_results_cols += [
                        (platform, result_type)
                        for platform in short_platforms
                        for result_type in self._all_result_types
                    ]
                    df = pd.DataFrame(
                        columns=pd.MultiIndex.from_tuples(nested_results_cols)
                    )
                ptf_res = []
                for platform, results in project["results"].items():
                    for check_type, check_values in self.result_types.items():
                        for result_type, result_name in check_values.items():
                            try:
                                ptf_res.append(results[check_type][result_name])
                            except TypeError:
                                ptf_res.append("UNKNOWN")
                df.loc[len(df.index)] = [
                    project["name"],
                    *ptf_res,
                ]
        return (df, parsed["date"])

    @request
    def check_status(
        self,
        date_to_check: date = date.today(),
    ):
        parsed_date = date_to_check.strftime(self.date_format)
        for slot, build_id in self._slots.items():
            msg = ""
            tmp_build_id = build_id
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
                    if df.empty or prdate > date_to_check:
                        tmp_build_id -= 1
                        continue
                    elif prdate < date_to_check:
                        msg = f"No {slot} available on {parsed_date}."
                        break
                    else:
                        msg += f"{slot}/{tmp_build_id}: \n"
                        msg += f"{df.to_string()}\n"
                        break
            except AttributeError as err:
                logging.warning(
                    f"Retrieving information for '{slot}/{build_id}' "
                    f" did not work. Error: '{err}'"
                )
                msg += "Something went wrong..."
            logging.info(msg)

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
