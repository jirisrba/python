import yaml
import requests
import json
import fileinput
import sys
import subprocess
import re

def parse_yaml():
    yaml_content = ''
    for line in fileinput.input(files=('-')):
        yaml_content = '{}{}'.format(yaml_content, line)
    
    return yaml.load(yaml_content)

def check_build(git_commit):
    config_data = parse_yaml()
    try:
        dbname = config_data['variables']['database']
        r = requests.get('http://172.17.0.1:8000/CheckBuild/{}'.format(dbname))
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
        project_re = re.search('^M\s+configuration.yaml$', status_and_file)
        if not project_re:
            print('This commit contains modifications not present in the last tested commit: {}, offending item: {}'.format(lesser_commit, status_and_file))
            return False
        else:
            if not compare_yaml(lesser_commit, git_commit):
                return False
    
    return True

'''
git diff --minimal 55119308b490c5a620e23665e8ed1b2e23f6715f 85a9a54765822680556fb39cccd53ba7c79421ae  configuration.yaml
diff --git a/configuration.yaml b/configuration.yaml
index c54f4a2..fbb67b4 100644
--- a/configuration.yaml
+++ b/configuration.yaml
@@ -1,5 +1,5 @@
 variables:
-  database: SBANKDEV2
+  database: S24DTA2
   app: Starbank
   user: SYS
'''
def compare_yaml(lesser_commit, git_commit):
    exec_str = 'git diff --minimal {} {} -- configuration.yaml 2>&1'.format(lesser_commit, git_commit)
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

if __name__ == '__main__':    
    if not check_build(sys.argv[1]):
        sys.exit(1)
