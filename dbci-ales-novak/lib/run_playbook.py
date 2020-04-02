from ansible import playbook, callbacks

# uncomment the following to enable silent running on the playbook call
# this monkey-patches the display method on the callbacks module
# callbacks.display = lambda *a,**ka: None

# the meat of the meal.  run a playbook on a path with a hosts file and ssh key
def run_playbook(playbook_path, hosts_path, key_file):
    stats = callbacks.AggregateStats()
    playbook_cb = callbacks.PlaybookCallbacks(verbose=0)
    runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=0)
    playbook.PlayBook(
        playbook=playbook_path,
        host_list=hosts_path,
        stats=stats,
        forks=4,
        callbacks=playbook_cb,
        runner_callbacks=runner_cb,
        private_key_file=key_file
        ).run()
    return stats


if __name__ == '__main__':
    stats = run_playbook(
        playbook_path='/dba/local/ansible/dbci-test.yaml',
        hosts_path='/dba/local/ansible/inventory/hosts',
        key_file='/home/oracle/.ssh/id_rsa.pub',
        )

    print "PROC", stats.processed
    print "FAIL", stats.failures
    print "OK  ", stats.ok
    print "DARK", stats.dark
    print "CHGD", stats.changed
    print "SKIP", stats.skipped
