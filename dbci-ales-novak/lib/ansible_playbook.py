# -*- coding: utf-8 -*-
import json

import ansible.release
from ansible.parsing.splitter import parse_kv
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.cli import CLI

from ansible.utils.vars import load_extra_vars
from ansible.utils.vars import load_options_vars

from ansible.plugins.callback.default import CallbackModule as CallbackModule_default

import os
import logging
from datetime import datetime
from collections import namedtuple

global_return_code = 0


class CallbackModule(CallbackModule_default):  # pylint: disable=too-few-public-methods,no-init
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'dbci'

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.task_name = task.get_name()
        super(CallbackModule, self).v2_playbook_on_task_start(task, is_conditional)

    def _dump_results(self, result):
        if "DBCI" in self.task_name and "cmd" in result:
            output = "DBCI:\n"
            if isinstance(result["cmd"], basestring):
                output += "cmd: {}\n".format(result["cmd"])
            elif isinstance(result["cmd"], tuple) or isinstance(result["cmd"], list):
                output += "cmd: {}\n".format(" ".join(result["cmd"]))
            else:
                output += "cmd: {}\n".format(result["cmd"])
            if "start" in result and "end" in result and "delta" in result:
                output += "start:{}\nend:{}\ntaken:{}\n".format(
                    result["start"],
                    result["end"],
                    result["delta"],
                )
            if "rc" in result:
                output += "rc: {}\n".format(result["rc"])
            if "stdout" in result:
                if len(result["stdout"]) != 0:
                    output += "stdout:\n{}".format(result["stdout"])
                else:
                    output += "stdout: <empty>\n"
            if output[-1] != "\n":
                output += "\n"
            if "stderr" in result:
                if len(result["stderr"]) != 0:
                    output += "stderr:\n{}".format(result["stderr"])
                else:
                    output += "stderr:<empty>\n".format(result["stderr"])
            if output[-1] != "\n":
                output += "\n"
            if "results" in result:
                output += "items:"
                for r in result["results"]:
                    output += "- {}\n".format(r["item"])
        else:
            output = CallbackModule_default._dump_results(self, result)
        return output

#class Options(object):
#    def __init__(self):
#        self.connection = "ssh"
#        self.forks = 8
#        self.check = False
#        self.become = None
#        self.become_method = None
#        self.become_user=None
#    def __getattr__(self, name):
#        return None

#def run_adhoc(ip,order):
#    variable_manager.extra_vars={"ansible_ssh_user":"root" , "ansible_ssh_pass":"passwd"}
#    play_source = {"name":"Ansible Ad-Hoc","hosts":"%s"%ip,"gather_facts":"no","tasks":[{"action":{"module":"command","args":"%s"%order}}]}
##    play_source = {"name":"Ansible Ad-Hoc","hosts":"192.168.2.160","gather_facts":"no","tasks":[{"action":{"module":"command","args":"python ~/store.py del"}}]}   
#    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)
#    tqm = None
#    callback = ResultsCollector()
#
#    try:
#        tqm = TaskQueueManager(
#            inventory=inventory,
#            variable_manager=variable_manager,
#            loader=loader,
#            options=options,
#            passwords=None,
#            run_tree=False,
#        )
#        tqm._stdout_callback = callback
#        result = tqm.run(play)
#        return callback
#
#    finally:
#        if tqm is not None:
#            tqm.cleanup()

def run_playbook(playbook, extra_vars=None, inventory_sources=None):

    print("The playbook {} started at {}".format(
        playbook, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    Options = namedtuple("Options", [
        "connection",
        "forks",
        "module_path",
        "become",
        "become_method",
        "become_user",
        "check",
        "diff",
        "listhosts",
        "listtasks",
        "listtags",
        "syntax",
    ])
    options = Options(
        connection="ssh",
        forks=8,
        module_path=None,
        become=None,
        become_method=None,
        become_user=None,
        check=False,
        diff=False,
        listhosts=False,
        listtasks=False,
        listtags=False,
        syntax=False,
    )
    passwords = {}

    if os.sep not in playbook:
        playbook = os.path.join(os.sep, "dba", "local", "ansible", playbook)

    if inventory_sources is None:
        inventory_path = os.path.join(os.path.dirname(playbook), "inventory", "hosts")
        if os.path.exists(inventory_path) and os.path.isfile(inventory_path):
            inventory_sources = [inventory_path]

    loader = DataLoader()
    inventory = InventoryManager(loader=loader, sources=inventory_sources)
    variable_manager = VariableManager(loader=loader, inventory=inventory)
    variable_manager.extra_vars=extra_vars
    variable_manager.options_vars = load_options_vars(options, CLI.version_info(gitinfo=False))
    callback = CallbackModule()

    pbex = PlaybookExecutor(
        playbooks=[playbook],
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        options=options,
        passwords=passwords,
    )
    pbex._tqm._stdout_callback = callback

    try:
        result = pbex.run()
        print("The playbook {} finished at {}".format(
            playbook, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        return result
    except Exception as e:
        print e
        print("The playbook {} failed at {}".format(
            playbook, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        raise e

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description="Run an Ansible playbook in the CSAS environment",
    )
    parser.add_argument("-i", "--inventory",  help="an Ansible inventory filename")
    parser.add_argument("-e", "--extra_vars", help="variables e.g. server=localhost db=ORACLE")
    parser.add_argument("playbook", help="an Ansible playbook filename")
    args = parser.parse_args()

    exit(run_playbook(args.playbook, parse_kv(args.extra_vars), args.inventory))
