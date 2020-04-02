import sys
import re
import os

project_user_matrix = dict([('Starbank', ('ano', 'starbankdev')), ('S24', ('ano', 's24dev'))])

def run():
    while True:
        status_and_name = sys.stdin.readline()
        if status_and_name == '':
            break

        ''' D    Starbank'''
        if re.match('^D\s+(?!.*/).*$', status_and_name):
            check_access_control('remove_top_level_dir', status_and_name)

        top_level_project = get_top_level(status_and_name)
        if top_level_project != None:
            check_access_control('git_update', top_level_project)

def check_access_control(permission, project):
    user = os.environ['GL_USERNAME']
    if  permission == 'remove_top_level_dir':
        if (user != 'ano'):
            drain_stdin()
            raise Exception('Operation: {} not permited for user: {}'.format(permission, user))

    if  permission == 'git_update':
        project_users = project_user_matrix[project]
        if project_users == None or len(project_users) == 0:
            drain_stdin()
            raise Exception('No users allowed for project: {}'.format(project))
        if not user in project_users:
            drain_stdin()
            raise Exception('User {} not allowed for project: {}'.format(user, project))

def drain_stdin():
    while True:
        forget_me = sys.stdin.readline()
        if forget_me == '':
            break
    

'''
Returns None for top level ops: 'A        S24'
'''
def get_top_level(status_name_line):
    project_re = re.search('^(A|D|M)\s+(.*?)/(.*)$', status_name_line)
    if project_re:
        project = project_re.group(2)
        if project == None or len(project) == 0:
            project = project_re.group(3)
        return project
    return None

if __name__ == '__main__':
    run()
                              
