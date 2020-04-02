import sys
import re
import os
import yaml
import subprocess
import requests
import json
import urllib
from requests.auth import HTTPBasicAuth

def parse_yaml(fpath):
    with open(fpath) as fstream:
        return yaml.load(fstream)

def get_api_data(db_name):    
    r = requests.get('https://oem12.vs.csin.cz:1528/ords/api/v1/db/{}'.format(db_name), auth=HTTPBasicAuth('dashboard', 'abcd1234'), verify='/etc/ssl/certs/ca-bundle.crt')
    return json.loads(r.text)

def run_exim():
    connection_params = parse_yaml('oracle-ci.yml')
    db_from = connection_params['variables']['database_from']
    db_to = connection_params['variables']['database_to']
    datapump_dir = connection_params['variables']['datapump_dir']
    
    db_from_info = get_api_data(db_from)
    print(db_from_info)
    db_to_info = get_api_data(db_to)
    print(db_to_info)
    
    # print('{} {} {} {} {}'.format(db_from, db_to, datapump_dir))

if __name__ == '__main__':
    run_exim()

