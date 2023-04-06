from extractor import find_links_in_dir

base = 'https://docs.kadaster.nl/pdok/interne-documentatie'
inspect_path = '/Users/williamloosman/repo/pdok/interne-documentatie'
# inspect_path = '/Users/williamloosman/repo/pdok/interne-documentatie/architectuur/applicaties'
output_file_name = 'links-in-docu'

links = find_links_in_dir(inspect_path, base_url=base, output_file_name='links')
