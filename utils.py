import requests
import logging


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
