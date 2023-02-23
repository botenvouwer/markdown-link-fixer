import fileinput
import json
import re

from link import Link

input_file = 'links.json'
pattern = re.compile(r'github\.com/PDOK/')
do_replace = True
replace_with = 'docs.kadaster.nl/pdok'

with open(input_file, 'r') as f:
    links_json = f.read()


def replace_url(filename, url_regex, replacement_url, do_replace=False):

    with fileinput.FileInput(filename, inplace=True) as file:
        line_count = 0
        for line in file:
            line_count += 1
            if re.search(url_regex, line):

                print(f"Found URL in {filename.as_posix():<40}: l{line_count} -> replace with: {replacement_url}")

                if do_replace:
                    line = re.sub(url_regex, replacement_url, line)
                else:
                    print("Flag do_replace is not set to True. Skipping the URL replacement.")
            # print(line, end="")


links = json.loads(links_json, object_hook=lambda d: Link.from_json(d))

# loop over the Link objects
for link in links:

    if not link.success:
        replace_url(link.found_in_file, pattern, replace_with, do_replace=do_replace)
