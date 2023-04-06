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
        self._current_line_number = 0

        # In order to trace a line number we separate this iteration from the recursive one
        # self._walk_md_ast(self._ast, self._get_link_from_element)

        for ast_part in self._ast.children:
            self._current_line_number += 1
            self._go_deeper_if_needed(ast_part)

    # https://en.wikipedia.org/wiki/Abstract_syntax_tree
    def _walk_md_ast(self, md_ast: [Element], callback):
        for c in md_ast.children:
            callback(c)
            self._go_deeper_if_needed(c)

    def _go_deeper_if_needed(self, e: [Element]):
        if hasattr(e, 'children') and isinstance(e.children, list) and len(e.children) > 0 and not isinstance(e, AutoLink):
            self._walk_md_ast(e, self._get_link_from_element)

    @staticmethod
    def _is_one_of(e, types):
        for t in types:
            if isinstance(e, t):
                return True

        return False

    def _get_link_from_element(self, e: [Element]):
        if self._is_one_of(e, self.types):
            l = Link(e.dest, type(e).__name__, base_url=self._base_url, url_filters=self.url_filters, found_in_file=self._path, found_on_line=self._current_line_number)
            self.link_list.append(l)

        if isinstance(e, RawText):
            self._find_urls_in_raw_text(e)

    def _find_urls_in_raw_text(self, e: RawText):
        text = e.children

        results = re.findall("(?P<url>https?://[^\s]+)", text)

        if len(results) > 0:
            for r in results:
                l = Link(r, 'RawTextLink', base_url=self._base_url, url_filters=self.url_filters, found_in_file=self._path, found_on_line=self._current_line_number)
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
            ['actual_url', 'url', 'type', 'success', 'status', 'httpStatus',
             'found_in_file', 'last_editor', 'last_edit_date'])

        save_me = []
        for path in pathlib.Path(inspect_path).rglob('*.md'):
            links = LinkExtractor(path, base_url=base)

            for link in links:
                link.test()
                link.resolve_last_editor()
                save_me.append(link.__dict__)

                writer.writerow(
                    [link.actual_url, link.url, link.type, link.success,
                     link.status, link.httpStatus, link.found_in_file.relative_to(inspect_path.parent),
                     link.last_editor, link.last_edit_date])
                print(link)

    with open(output_file_name+'.json', 'w', encoding='utf-8') as f:
        pickle = jsonpickle.encode(save_me, unpicklable=False)
        parsed_json = json.loads(pickle)
        json.dump(parsed_json, f, ensure_ascii=False, indent=4)

    return save_me
