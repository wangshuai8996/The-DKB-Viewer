from .common import client_exception as E

mapping = {
        'local': 'http://127.0.0.1:5000',
        'ex3KB': 'http://127.0.0.1:5000',
        }

def import_setting(filename):
    import ruamel.yaml as yaml
    with open(filename, 'r') as stream:
        yml = yaml.safe_load(stream)
        mapping.update(yml['servers'])

def get_site(site):
    if site.startswith('http://') or site.startswith('https://'):
        return site
    if site in mapping:
        return mapping[site]
    else:
        raise E.DKBnotFoundError(f"The requested DKB site {site} could not be found")
