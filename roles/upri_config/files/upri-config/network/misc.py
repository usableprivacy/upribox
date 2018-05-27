from lib.utils import call_ansible, write_role

# return values:
# 10: invalid argument


def action_set_ssh(arg):
    if arg not in ['yes', 'no']:
        print 'error: only "yes" and "no" are allowed'
        return 10
    print 'ssh enabled: %s' % arg
    en = {"general": {"enabled": arg}}
    write_role('ssh', en)


def action_restart_ssh(arg):
    print 'restarting ssh...'
    return call_ansible('toggle_ssh')
