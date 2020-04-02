# Database Continue Integration

Integrace a automatizace pozadavku na systemovou podporu databasi CS.

## Getting Started


### Run a sql script

TODO: doplni p. Ales Novak


### Run an ansible playbook

* ansible-ci.yaml:

```yaml
variables:
  server: boem,todbrca1
  db: ORACLE

stage:
- deploy

playbooks:
- dbci-test.yaml
```

* deploy.py:

```python
#!/usr/bin/env python2

import yaml
from lib.ansible_playbook import ansible_playbook

ci = yaml.load(open("ansible-ci.yaml"))
for playbook in ci["playbooks"]:
    ansible_playbook(playbook, extra_vars=ci["variables"])
```

## Install

Po kazdem `git push` je aktualni verse ulozena do `omsgc:/dba/local/dbci/`
(Jenkins project **dbci-jenkins-integration**)


## Appendix
