
try:
    import aiohttp
except ImportError:
    msg = "The aiohttp package must be installed to use this feature"
    raise RuntimeError(msg)

import re

from .github import confirm_GitHub, fetch_GitHub, parse_URI

LICENSE_MAP = {'Commercial': 'Commercial Software',
               'No License': 'Proprietary/Copyrighted',
               'Freemium': 'Other',
               'Freeware': 'Other',
               'Non-commercial': 'Other',
               'Government Use': 'Other',
               'Other': 'Other'}

OS_MAP = {'GPL': 'GNU General Public License v3.0',
          'LGPL': 'GNU Lesser General Public License v2.1',
          'AGPL': 'GNU Affero General Public License v3.0',
          'CeCILL': 'Other',
          'MIT': 'MIT License',
          'BSD': "BSD 3-Clause 'New' or 'Revised' License",
          'Apache': 'Apache License 2.0',
          'The Unlicense': 'The Unlicense',
          'Other': 'Other'}

LANGUAGE_MAP = {'C': 'Other',
                'C++': 'C++',
                'Fortran': 'Fortran',
                'Java': 'Other',
                'JavaScript': 'JavaScript',
                'MATLAB': 'MATLAB',
                'Other': 'Other',
                'Python': 'Python',
                'R': 'Other'}

def get_category_pages(site, category_name, route=None):
    
    category = site.categories[category_name]
    
    if route is None:
        route = ""
        test = lambda x: True
    else:
        test = lambda x: route in x.name
    
    return [page.name.replace(route, "")
                                for page in category if route in page.name]


def compare_titles(page_titles, db):
    
    db_titles = [x['value'].lower() for x in db.projection('Title')['Title']]
    matched = [x for x in page_titles if x.lower() in db_titles]
    unmatched = list(set(page_titles) - set(matched))
    
    return matched, unmatched


def page_to_fields(page):
    
    result = re.search(r'{{(.*?)}}', page, flags=re.DOTALL)
    data = result.group(1)
    records = [record.rstrip() for record in data.split('|')[1:]]
    fields = {k: v for k, v in [record.split("=") for record in records]}
    
    return fields


async def upload_records_to_site(db,
                                 site,
                                 route,
                                 skip_category=None,
                                 skip=None,
                                 dry_run=False):
    
    if skip is None: skip = []
    if skip_category is not None:
        names = get_category_pages(site, skip_category, route)
        matched, _ = compare_titles(names, db)
        skip += matched
    
    for record in db.to_records().values():
        
        title, fields = title_and_fields_from_record(record)
        
        if title in skip:
            print(f"Skipping matching title {title}")
            continue
        
        if fields["URI"] == "Unknown":
            print(f"{title} has no URI. Skipping.")
            continue
        
        await update_fields_from_github(fields)
        text = fields_to_page(fields)
        
        print(f"Loading {title} to {route + title}")
        
        if not dry_run:
            page = site.pages[route + title]
            page.edit(text, f'Add {title}')
        
        print("Success")


def title_and_fields_from_record(record):
    
    title = record.find_by_path("Title").value
    fields = {'URI': 'Unknown',
              'mreDatasubtype': 'Unknown',
              'description': '',
              'tags': '',
              'author': 'Unknown',
              'originationDate': 'Unknown',
              'mreTechnologyType': 'Unknown',
              'license': 'Unknown',
              'devLanguage': 'Unknown',
              'version': 'Unknown'}
    entry_type = None
    
    root_children_names = [child.name for child in record.root_node.children]
    
    if "Web Address" in root_children_names:
        fields["URI"] = record.find_by_path("Title/Web Address").value
    
    if "Developer" in root_children_names:
        fields["author"] = record.find_by_path("Title/Developer").value

    if "Technology" in root_children_names:
        tech = [child.name
                for child in record.find_by_path("Title/Technology").children]
        fields["mreTechnologyType"] = tech
        
    if "License Type" in root_children_names:
        licenses = get_licenses(record)
        fields["license"] = licenses
        if "Commercial" in licenses:
            entry_type = "Commercial Software"
    
    if "Programming Language" in root_children_names:
        languages = get_languages(record)
        fields["devLanguage"] = languages
    
    tags = [child.name for child in
                            record.find_by_path("Title/Life Cycle").children]
    
    if "Discipline" in root_children_names:
        tags += [child.name for child in
                            record.find_by_path("Title/Discipline").children]
    
    fields["tags"] = tags
    
    if entry_type is None and "Interface" in root_children_names:
        interfaces = [child.name
                for child in record.find_by_path("Title/Interface").children]
        if set(["web-API", "Web Page"]) & set(interfaces):
            entry_type = "API"
    
    if entry_type is None:
        entry_type = "Public Repo (e.g. public git repo)"
    
    fields["mreDatasubtype"] = entry_type
    fields["description"] = ""
    fields['originationDate'] = "Unknown"
    fields['version'] = "Unknown"
    
    return title, fields


def get_licenses(record):
    
    get_children = lambda x: record.find_by_path(x).children
    
    root = [child.name for child in record.root_node.children]
    if "License Type" not in root: return None
    
    licenses = []
    top = [child.name for child in get_children("Title/License Type")]
    
    for lic in top:
        if lic == "Open-Source": continue
        licenses.append(LICENSE_MAP[lic])
            
    if "Open-Source" not in top:
        return licenses
        
    os = [child.name
                for child in get_children("Title/License Type/Open-Source")]
    
    for lic in os:
        licenses.append(OS_MAP[lic])
    
    return licenses


def get_languages(record):
    
    get_children = lambda x: record.find_by_path(x).children
    
    root = [child.name for child in record.root_node.children]
    if "Programming Language" not in root: return None
    
    languages = []
    top = [child.name for child in get_children("Title/Programming Language")]
    
    for lang in top:
        languages.append(LANGUAGE_MAP[lang])
               
    return languages


async def update_fields_from_github(fields):
    
    if not confirm_GitHub(fields['URI']):
        return
    
    uri_details = parse_URI(fields['URI'])
    result = await fetch_GitHub(uri_details)
    
    fields['description'] = result['description']
    fields['tags'] = list(set(fields['tags']) | set(result['topics']))
    
    if result['created']:
        fields['originationDate'] = result['created'].strftime("%Y/%m/%d")
    
    if result['version']:
        fields['version'] = result['version']


def fields_to_page(fields, page=None):
    
    str_fields = {k: ", ".join(v) if isinstance(v, list) else v
                                                for k, v in fields.items()}
    records = "\n".join([f"|{k}={v}" for k, v in str_fields.items()])
    data = "{{MRE Code\n" + records + "\n}}"
    
    if page is None:
        page = data + "\n"
    else:
        page = re.sub(r'{{(.*?)}}', data, page, flags=re.DOTALL)
    
    return page
