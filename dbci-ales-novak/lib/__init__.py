"""
Knihovna pro intergraci CSAS DB Ansible

usage:
~~~ ansible-ci.yaml ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
variables:
  server: boem,todbrca1
  db: ORACLE

stage:
- deploy

playbooks:
- test-dbci.yaml
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

~~~ deploy.py ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#!/usr/bin/env python2

import yaml
from lib.ansible_playbook import ansible_playbook


ci = yaml.load(open("ansible-ci.yaml"))
print ci
for playbook in ci["playbooks"]:
    ansible_playbook(playbook, extra_vars=ci["variables"])
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

./deploy.py

"""
