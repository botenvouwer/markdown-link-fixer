from extractor import LinkExtractor, find_links_in_dir

base = 'https://docs.kadaster.nl/pdok/interne-documentatie'
inspect_path = '/Users/williamloosman/repo/pdok/interne-documentatie'
output_file_name = 'links'

links = find_links_in_dir(inspect_path, base_url=base, output_file_name='links')
