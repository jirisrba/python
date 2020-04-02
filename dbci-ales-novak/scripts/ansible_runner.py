#!/usr/bin/env python3

import sys
import yaml
import requests
import json
from requests.auth import HTTPBasicAuth
from lib.ansible_playbook import run_playbook

def get_api_data(dbname):
    #/dba/local/dbci/ords_certfile
    r = requests.get('https://oem12.vs.csin.cz:1528/ords/api/v1/db/{}'.format(dbname), auth=HTTPBasicAuth('dashboard', 'abcd1234'), verify=False)
    if r.status_code >= 200 and r.status_code < 300:
        json_map = json.loads(r.text)
        #print('Host name: {}'.format(str(json_map['host_name'])))
        return [str(json_map['app_name'][0]), str(json_map['env_status']),str(json_map['server_name'])]
    return ['', '', '']

ci = yaml.load(open(sys.argv[1]))

# stage controls
if not isinstance(ci['stage'], list):
    print('Stage is not a list but: {} type'.format(type(ci['stage'])))
    sys.exit(1)

stage = ci['stage'][0]
if stage != 'deploy':
    print('Stage is not deploy but: {}'.format(stage))
    sys.exit(1)

# playbook controls
if not isinstance(ci['playbooks'], list):
    print('Playbooks is not a list but: {} type'.format(type(ci['playbooks'])))
    sys.exit(1)
else:
    for pbook in ci['playbooks']:
        if not isinstance(pbook, str):
            print('playbook content is not a string but: {} type'.format(type(pbook)))
            sys.exit(1)

#variables controls
variables_list = ci['variables']
if not isinstance(variables_list, list):
    print('variables is not a list but: {} type'.format(type(variables_list)))
    sys.exit(1)

for variables in variables_list:
    if not isinstance(variables, dict):
        print('inner variables content is not a dictionary but: {} type'.format(type(variables)))
        sys.exit(1)

    dbname = variables['db']
    server = variables['server']
    app_name, env_status, server_name = get_api_data(dbname)
    print('DB env status: {}'.format(env_status))
    if env_status == 'Production':
        print('Cannot use production system DB: {}'.format(dbname))
        sys.exit(1)

    if server.lower() != server_name.lower() and '{}.vs.csin.cz'.format(server.lower()) != server_name.lower():
        print('Provided server name: {} differs from registered server name from API db: {}'.format(server, server_name))
        sys.exit(1)

global_rc = 0
for variables in variables_list:
    for playbook in ci["playbooks"]:
        rc = run_playbook(playbook, extra_vars=variables)
        global_rc += rc

exit(global_rc)
