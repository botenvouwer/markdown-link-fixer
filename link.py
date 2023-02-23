import re
from pathlib import PosixPath, Path
from urllib.parse import urlparse, urljoin

import jsonpickle
import requests as requests
from jsonpickle.handlers import BaseHandler


class Link:

    _default_positive_status_codes = [200]

    def __init__(self, url, link_type, base_url=None, positive_status_codes=None, url_filters=None):
        self.base_url = base_url
        self.url = url
        self.actual_url = self.get_url()
        self.type = link_type
        self._positive_status_codes = positive_status_codes if positive_status_codes is not None else self._default_positive_status_codes
        self.success = False
        self.status = None
        self.httpStatus = None
        self._found_in_file = None
        self._url_filters = url_filters if url_filters is not None else []

    @classmethod
    def from_json(cls, json_dict):
        link = Link(None, None)

        for key, value in json_dict.items():
            link[key] = value

        return link

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __str__(self):
        file = '-' if self.found_in_file is None else self.found_in_file.name
        return f"{file:<40}{self.type:<15}{self.status:<20}{self.get_url()}"

    @property
    def found_in_file(self) -> Path:
        return Path(self._found_in_file)

    @found_in_file.setter
    def found_in_file(self, value):
        self._found_in_file = Path(value)

    def is_absolute(self, url=None):
        url = url if url is not None else self.url
        return bool(urlparse(url).netloc)

    def get_url(self):

        if not self.is_absolute():
            if self.base_url is None:
                return self.url
            return urljoin(self.base_url, self.url)

        return self.url

    def test(self):

        url = self.get_url()

        if url is None:
            self.status = 'Empty or unusual url'
            return

        if not self.is_absolute(url):
            self.status = 'Relative url'
            return

        for regex in self._url_filters:
            if re.search(regex, url):
                self.status = 'Filter: ' + regex
                self.success = True
                return

        try:
            r = requests.get(url)
            self.httpStatus = r.status_code

            if self.httpStatus in self._positive_status_codes:
                self.status = 'Success'
                self.success = True
            else:
                self.status = 'Failed'

        except requests.ConnectionError:
            self.status = 'Failed to connect'
        except requests.exceptions.InvalidURL:
            self.status = 'InvalidURL'
        except Exception as e:
            self.status = 'Error'


class PathHandler(BaseHandler):
    def restore(self, obj):
        return Path(obj)

    def flatten(self, obj, data):
        return str(obj.as_posix())


jsonpickle.handlers.registry.register(PosixPath, PathHandler)
