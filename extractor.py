import csv
import json
import re
from typing import Union

import jsonpickle
import marko
import pathlib

from marko import inline
from marko.block import LinkRefDef
from marko.element import Element
from marko.inline import Image, AutoLink, RawText

from link import Link


class LinkExtractor:
    _default_url_filters = [
        'localhost',
        'mailto',
        '\.\.\.pdok\.nl',
    ]

    types = [
        LinkRefDef,
        inline.Link,
        Image,
        AutoLink
    ]

    def __init__(self, p: Union[pathlib.Path, str], base_url: str = None, url_filters=None):
        self._path = pathlib.Path(p)
        self._base_url = base_url
        self._ast = marko.parse(self._path.read_text())
        self.link_list: [Link] = []
        self.url_filters = url_filters if url_filters is not None else self._default_url_filters

        self._walk_md_ast(self._ast, self._get_link_from_element)

    # https://en.wikipedia.org/wiki/Abstract_syntax_tree
    def _walk_md_ast(self, md_ast: [Element], callback):
        for c in md_ast.children:
            callback(c)

            if hasattr(c, 'children') and isinstance(c.children, list) and len(c.children) > 0 and not isinstance(c, AutoLink):
                self._walk_md_ast(c, self._get_link_from_element)

    @staticmethod
    def _is_one_of(e, types):
        for t in types:
            if isinstance(e, t):
                return True

        return False

    def _get_link_from_element(self, e: [Element]):
        if self._is_one_of(e, self.types):
            l = Link(e.dest, type(e).__name__, base_url=self._base_url, url_filters=self.url_filters)
            self.link_list.append(l)

        if isinstance(e, RawText):
            self._find_urls_in_raw_text(e)

    def _find_urls_in_raw_text(self, e: RawText):
        text = e.children

        results = re.findall("(?P<url>https?://[^\s]+)", text)

        if len(results) > 0:
            for r in results:
                l = Link(r, 'RawTextLink', base_url=self._base_url, url_filters=self.url_filters)
                self.link_list.append(l)

    def __iter__(self):
        return iter(self.link_list)


def find_links_in_dir(dir: Union[pathlib.Path, str], base_url: str = None, output_file_name='links'):
    dir = pathlib.Path(dir)

    base = base_url
    inspect_path = dir

    with open(output_file_name+'.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(
            ['base_url', 'url', 'actual_url', 'type', 'success', 'status', 'httpStatus',
             'found_in_file'])

        save_me = []
        for path in pathlib.Path(inspect_path).rglob('*.md'):
            links = LinkExtractor(path, base_url=base)

            for link in links:
                link.test()
                link._found_in_file = path
                save_me.append(link.__dict__)

                writer.writerow(
                    [link.base_url, link.url, link.actual_url, link.type, link.success,
                     link.status, link.httpStatus, link._found_in_file])
                print(link)

    with open(output_file_name+'.json', 'w', encoding='utf-8') as f:
        pickle = jsonpickle.encode(save_me, unpicklable=False)
        parsed_json = json.loads(pickle)
        json.dump(parsed_json, f, ensure_ascii=False, indent=4)

    return save_me
