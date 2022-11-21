import requests
import logging
import re


def request(get_response):
    def wrapper(*args, **kwargs):
        try:
            get_response(*args, **kwargs)
        except requests.exceptions.HTTPError as err:
            msg = (
                "Something went wrong trying to access the "
                "LHCb nightly configuration website. "
                "Please, check that you typed in correct URL"
                " and that you have internet access."
            )
            logging.error(msg)
            raise err

    return wrapper


def color_values(value: str):
    color = "black"
    if re.search(r"(?:E:|F:)0", value):
        color = "green"
    if re.search(r"W:[1-9][0-9]{0,3}", value):
        color = "orange"
    if re.search(r"(?:E:|F:)[1-9][0-9]{0,3}", value):
        color = "red"
    return f"color: {color}"
