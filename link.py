import os
import re
import subprocess
from datetime import datetime
from pathlib import PosixPath, Path
from urllib.parse import urlparse, urljoin

import jsonpickle
import requests as requests
from jsonpickle.handlers import BaseHandler


class Link:

    _default_positive_status_codes = [200]

    def __init__(self, url, link_type, base_url=None, positive_status_codes=None, url_filters=None, found_in_file=None, found_on_line=None):
        self.base_url = base_url
        self.url = url
        self.actual_url = self.get_url()
        self.type = link_type
        self._positive_status_codes = positive_status_codes if positive_status_codes is not None else self._default_positive_status_codes
        self.success = False
        self.status = None
        self.httpStatus = None
        self._found_in_file = found_in_file
        self.found_on_line = found_on_line
        self._last_editor = None
        self._last_edit_date = None
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

    def _resolve_last_editor(self):
        original_dir = os.getcwd()
        os.chdir(self._found_in_file.parent.as_posix())

        if self.found_on_line is None:
            output = subprocess.check_output(["git", "log", "-1", "--format=%cn#s#%cd", "--", self._found_in_file.as_posix()])
            output_parts = output.decode("utf-8").split("#s#")
            self._last_editor, self._last_edit_date = output_parts[0].strip(), output_parts[1].strip()
        else:
            output = subprocess.check_output(['git', 'blame', '--porcelain', '-L', str(self.found_on_line) + "," + str(self.found_on_line), self._found_in_file.as_posix()],
                                             universal_newlines=True)
            committer = None
            commit_date_time = None

            for line in output.split('\n'):
                if line.startswith('committer '):
                    committer = line[10:]
                elif line.startswith('committer-time '):
                    unix_timestamp = int(line[15:])
                    # todo: include timezone
                    commit_date_time = datetime.utcfromtimestamp(unix_timestamp).strftime('%a %b %d %H:%M:%S %Y +0000')

            self._last_editor = committer
            self._last_edit_date = commit_date_time

        os.chdir(original_dir)

    def resolve_last_editor(self):
        self._resolve_last_editor()

    @property
    def last_edit_date(self):
        if self._last_edit_date is None:
            self._resolve_last_editor()

        return self._last_edit_date

    @last_edit_date.setter
    def last_edit_date(self, value):
        self._last_edit_date = value

    @property
    def last_editor(self):
        if self._last_editor is None:
            self._resolve_last_editor()

        return self._last_editor

    @last_editor.setter
    def last_editor(self, value):
        self._last_editor = value


class PathHandler(BaseHandler):
    def restore(self, obj):
        return Path(obj)

    def flatten(self, obj, data):
        return str(obj.as_posix())


jsonpickle.handlers.registry.register(PosixPath, PathHandler)
