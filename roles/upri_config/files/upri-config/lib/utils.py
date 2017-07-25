import json
import sys
import subprocess
from jsonmerge import merge
from os.path import join, exists
from lib.settings import FACTS_DIR, ANSIBLE_COMMAND, ANSIBLE_INVENTORY, ANSIBLE_PLAY, DEFAULTS

#
# calls ansible and executes the given tag locally
#


def call_ansible(tag):
    return subprocess.call([ANSIBLE_COMMAND, '-i', ANSIBLE_INVENTORY, ANSIBLE_PLAY, "--tags", tag, "--connection=local"])

#
# write the custom json "data" to the fact with the given name "rolename"
#


def write_role(rolename, data, schema={}):
    p = join(FACTS_DIR, rolename + '.fact')
    try:
        with open(p, 'r') as data_file:
            js = json.load(data_file)
    except IOError:
        js = {}

    js = merge(js, data, schema)
    with open(p, 'w+') as data_file:
        json.dump(js, data_file, indent=4)


def get_fact(role, group, fact=None):
    if exists(FACTS_DIR):
        try:
            with open(join(FACTS_DIR, role + ".fact")) as file:
                data = json.load(file)
                if fact:
                    erg = data[group][fact] if group in data and fact in data[group] else None
                else:
                    erg = data[group] if group in data else None
                return erg
        except IOError as e:
            print 'Cannot read Local Facts File ' + role + ": " + e.strerror


def get_default(role, group, fact=None):
    try:
        with open(DEFAULTS, 'r') as f:
            data = json.load(f)

        if fact:
            erg = data[group][fact]
        else:
            erg = data[group]
        return erg
    except IOError as e:
        print 'Cannot read Defaults File ' + role + ": " + e.strerror
    except (KeyError, TypeError) as e:
        return None

def check_fact(role, group, fact=None):
    fact = get_fact(role, group, fact)
    if fact is not None:
        return fact
    else:
        return get_default(role, group, fact)
