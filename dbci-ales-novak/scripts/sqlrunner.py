'''
Created on Nov 8, 2017
@author: anovak
'''

import sys
import re
import os
import yaml
import subprocess
import requests
import json
import urllib
from requests.auth import HTTPBasicAuth
import fileinput

def parse_yaml(fpath):
    with open(fpath) as fstream:
        return yaml.load(fstream)

def run_security_check(connection_params, cwd):
    patts = read_patterns('/dba/local/dbci/scripts/patterns.txt')
    for sqlfile in connection_params['script']:
        sql_abs = '{}/{}'.format(cwd, sqlfile)
        if (is_children(cwd, sql_abs)):
            filter_sql(sqlfile, patts)

def create_command_string(connection_params, connect_string, cwd):
    sqlc_string_template = '/dba/sqlcl/bin/sql -oci \'/@{}\'  '
    if connection_params['variables']['user'] == 'SYS':
        sqlc_string_template = sqlc_string_template  + ' AS SYSDBA '
    sqlc_string_template = sqlc_string_template.format(connect_string)
    
    ret = ['echo "" > sql_run.log']
    for sqlfile in connection_params['script']:
        sql_abs = '{}/{}'.format(cwd, sqlfile)
        if (is_children(cwd, sql_abs)):
            ret.append('{} @{} >> sql_run.log'.format(sqlc_string_template, sqlfile))
            ret.append('if [ $? -ne 0 ] ; then')
            ret.append('    exit 1')
            ret.append('fi')
            ret.append('grep "Error starting at line" sql_run.log > /dev/null ')
            ret.append('if [ $? -eq 0 ] ; then')
            ret.append('    exit 1')
            ret.append('fi')
    return ret

'''
compares paths on filesystem
'''
def is_children(parent_path_to_test, child_path_to_test):
    if child_path_to_test != None and parent_path_to_test != None:
        preal = os.path.realpath(parent_path_to_test)
        chreal = os.path.realpath(child_path_to_test)
        if preal == chreal:
            return False
        if chreal.startswith(preal + os.sep):
            return True
        
    return False

def get_commit_message(git_commit):
    git_commit = re.sub(r'\s+', '', git_commit)
    exec_str = 'git show -s --format=%s%b {}'.format(git_commit)
    git_process = subprocess.Popen(exec_str, shell=True, stdout=subprocess.PIPE)
    comment = git_process.stdout.read()
    return comment.strip()

def notify_build_completed(git_commit, app_name, db_name, env_status):
    commit_message = get_commit_message(git_commit)
    data = {'appname': app_name, 'dbname': db_name, 'stage': env_status, 'commit_message': commit_message}
    r = requests.post('http://localhost:6000/SetBuildOk/{}'.format(git_commit), data=data)
    reply_json = json.loads(r.text)
    if 'oracle_error' in reply_json:
         print('Build runner got Oracle CX error:')
         print(str(reply_json['error_code']))
         print(str(reply_json['error_message']))
    elif 'error' in reply_json:       
         print(str(reply_json['error']))
    
    return str(reply_json['insert'])

def notify_build_failed(git_commit, db_name, log):
    data = {'dbname': db_name, 'log': log}
    r = requests.post('http://localhost:6000/SetBuildFailed/{}'.format(git_commit), data=data)
    #target_url = { 'target_url' : 'http://{}:8000/GetLog/{}/{}'.format(ip_addr, git_commit, db_name) }
    #target_url = urllib.urlencode(target_url)
    #project_path = urllib.quote_plus(project_path)
    #git_url = 'http://{}/api/v4/projects/{}/statuses/{}?state=failed&{}&context=dbbuild'.format(ip_addr, project_path, git_commit, target_url)
    #r = requests.post(git_url, headers = { 'PRIVATE-TOKEN': token } )
    #print(json.loads(r.text))

def get_connect_string(raw_text):
    return str(raw_text['connect_descriptor'])

def get_env_status(raw_data):
    return str(raw_data['env_status'])

def get_api_data(db_name):    
    r = requests.get('https://oem12.vs.csin.cz:1528/ords/api/v1/db/{}'.format(db_name), auth=HTTPBasicAuth('dashboard', 'abcd1234'), verify='/etc/ssl/certs/ca-bundle.crt')
    return json.loads(r.text)

def check_build(db_name, git_commit):
    try:
        r = requests.get('http://localhost:6000/CheckBuild/{}'.format(db_name))
        reply_json = json.loads(r.text)
        if 'error' in reply_json:
            print(str(reply_json['error']))
            return False
        if 'oracle_error' in reply_json:
             print('Oracle CX error:')
             print(str(reply_json['error_code']))
             print(str(reply_json['error_message']))
             return False
        if 'OK' in reply_json['build_status']:
            if 'git_commit' in reply_json:
                lesser_commit = str(reply_json['git_commit'])
                return compare(lesser_commit, git_commit)
            return True #dev env
    except KeyError as e:
        print('Invalid key: {}'.format(e))
        print('Invalid yaml data, database required: {}'.format(config_data))
    
    return False

def compare(lesser_commit, git_commit):
    exec_str = 'git diff-tree --no-commit-id --name-status -r {} {}'.format(lesser_commit, git_commit)
    git_process = subprocess.Popen(exec_str, shell=True, stdout=subprocess.PIPE)
    for status_and_file in git_process.stdout:
        status_and_file = status_and_file.decode('utf-8').rstrip()
        project_re = re.search('^M\s+oracle-ci.yml$', status_and_file)
        if not project_re:
            print('This commit contains modifications not present in the last tested commit: {}, offending item: {}'.format(lesser_commit, status_and_file))
            return False
        else:
            if not compare_yaml(lesser_commit, git_commit):
                return False
    
    return True

'''
git diff --minimal 55119308b490c5a620e23665e8ed1b2e23f6715f 85a9a54765822680556fb39cccd53ba7c79421ae  oracle-ci.yml
diff --git a/oracle-ci.yml b/oracle-ci.yml
index c54f4a2..fbb67b4 100644
--- a/oracle-ci.yml
+++ b/oracle-ci.yml
@@ -1,5 +1,5 @@
 variables:
-  database: SBANKDEV2
+  database: S24DTA2
   app: Starbank
   user: SYS
'''
def compare_yaml(lesser_commit, git_commit):
    exec_str = 'git diff --minimal {} {} -- oracle-ci.yml 2>&1'.format(lesser_commit, git_commit)
    git_process = subprocess.Popen(exec_str, shell=True, stdout=subprocess.PIPE)
    for line in git_process.stdout:
        line = line.decode('utf-8').rstrip()
        #print('compare.yaml: stdout line: {}'.format(line))
        modified_lines_re = re.search('^[\+-]\s+.*$', line)
        if modified_lines_re:
            database_re = re.search('^[\+-]\s+database:.*$', line)
            if not database_re:
                print('Only database target can change. The last tested commit with a lesser env_status is: {}, offending item: {}'.format(lesser_commit, line))
                return False
    #print('compare.yaml: No more lines')
    return True

def cat_file(fileName):
    result = ''
    with open(fileName, 'r') as sql_log:
        for line in sql_log:
            result += line
    sys.stdout.write(result)
    sys.stdout.flush()
    return result

def read_patterns(file_name):
    regexp = ''
    with open(file_name, 'r') as patterns_file:
        for line in patterns_file:
            line = line.rstrip('\r\n')
            if not re.match('(^\s*#.*)|(^$)', line):
                regexp_elems = line.split(' ')
                if len(regexp_elems) > 1 :
                    regexp = regexp + '|(.*{}\s+.*{}((\s|;)+.*))'.format(regexp_elems[0], regexp_elems[1])
                else:
                    regexp = regexp + '|(.*{}((\s|;)+.*))'.format(regexp_elems[0])
    
    if len(regexp) > 1:
        regexp = regexp[1:]
    
    return regexp

def filter_sql(file_name, regexp):
    regexp_program = re.compile(regexp, re.IGNORECASE)
    comments_program = re.compile('(^\s*--.*)|(^\s*//.*)')
    
    with open(file_name, 'r') as sql_file:
        for line in sql_file:
            line = line.rstrip('\r\n')
            if not comments_program.match(line):
                if regexp_program.match(line):
                    raise Exception('SQL Security: {}'.format(line))

def run_sql(cwd, git_commit):
    connection_params = parse_yaml('oracle-ci.yml')
    db_name = connection_params['variables']['database']
    app_name = connection_params['variables']['app']
    if not check_build(db_name, git_commit):
        print('Build is not allowed to be run on db: {}'.format(db_name))
        sys.exit(1)
    run_security_check(connection_params, cwd)
    raw_data = get_api_data(db_name)
    connect_string = get_connect_string(raw_data)
    command_list = create_command_string(connection_params, connect_string, cwd)
    with open('commands.sh', 'w+') as command_file:
        for command in command_list:
            command_file.write('{}{}'.format(command, '\n'))
    
    process = subprocess.Popen('sh ./commands.sh', shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
    process.wait()
    log = cat_file('sql_run.log')
    if process.returncode > 0:
        notify_build_failed(git_commit, db_name, log)
        sys.exit(1)
    
    ok_status = notify_build_completed(git_commit, app_name, db_name, get_env_status(raw_data))
    if ok_status == 'NOK':
        sys.exit(1)

if __name__ == '__main__':
    # 'path to Jenkins workspace', git_commit
    run_sql(sys.argv[1], sys.argv[2])
