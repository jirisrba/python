import sys
import re
import os

def run():
    projects_collection = []
    while True:
        status_name = sys.stdin.readline()
        if status_name == '':
            break
        
        top_level_project = get_top_level(status_name)
        if top_level_project != None:
            collect(projects_collection, top_level_project)
    
    for top_level_p in projects_collection:
        print(top_level_p)

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

def collect(projects_collection, project):
    if not project in projects_collection:
        projects_collection.append(project)
        
        
if __name__ == '__main__':    
    run()