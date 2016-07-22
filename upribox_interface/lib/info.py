import subprocess
import json


class HardwareInfo:
    def __init__(self):
        self.specs = self.get_hw_specs()
        self.model = self.get_hardware_model()
        self.wifi_devices = self.get_wireless_devices()

    @staticmethod
    def get_hw_specs():
        specs = None
        try:
            hw_specs = subprocess.check_output(['/usr/bin/lshw', '-json'])
            specs = json.loads(hw_specs)
        except subprocess.CalledProcessError:
            pass
        return specs

    def get_network_devices(self):
        try:
            network_devices = list()
            for hardware in self.specs['children']:
                if hardware['class'] == 'network':
                    network_devices.append(hardware)
            return network_devices
        except:
            return None

    def get_wireless_devices(self):
            network_devices = self.get_network_devices()
            wireless_devices = dict()
            try:
                for device in network_devices:
                    if 'wireless' in device['capabilities']:
                        wifi_device = {'driver': device['configuration']['driver'],
                                       'bus': device['businfo']}
                        wireless_devices[device['logicalname']] = wifi_device
                return wireless_devices
            except:
                return None

    def get_hardware_model(self):
        if 'product' in self.specs:
            return self.specs['product']
        else:
            return None

    def pi3_builtin_wifi_only(self):
        if self.model.contains('Pi 3') and len(self.wifi_devices) == 1:
            return True
        else:
            return False

    def __str__(self):
        return '\n'.join((self.model, str(self.wifi_devices)))


class UpdateStatus:

    ANSIBLE_PULL_LOG_FILE = '/var/tmp/log/ansible-pull.log'
    GIT_REPO_LOCAL_DIR = '/var/lib/ansible/local'

    def __init__(self):
        self.branch = None
        self.last_commit_short = None
        self.update_utc_time = None
        self.upgrade_successful = False

        self.get_upgrade_status()
        self.get_last_commit_short_hash()
        self.get_update_time()
        self.get_git_branch()

    def __str__(self):
        return '\n'.join((str(self.branch), str(self.last_commit_short), str(self.update_utc_time), str(self.upgrade_successful)))

    def get_git_branch(self):
        try:
            self.branch = subprocess.check_output(['/usr/bin/git', '-C', self.GIT_REPO_LOCAL_DIR, 'rev-parse', '--abbrev-ref', 'HEAD']).strip()
        except:
            pass

    def get_last_commit_short_hash(self):
        try:
            self.last_commit_short = subprocess.check_output(['/usr/bin/git', '-C', self.GIT_REPO_LOCAL_DIR, 'rev-parse', '--short', 'HEAD']).strip()
        except:
            pass

    def get_update_time(self):
        try:
            from os.path import getctime
            from datetime import datetime
            self.update_utc_time = datetime.utcfromtimestamp(getctime(self.ANSIBLE_PULL_LOG_FILE))
        except:
            pass

        """
               PLAY RECAP ********************************************************************\
               127.0.0.1                  : ok=168  changed=7    unreachable=0    failed=0'
        """

    def get_upgrade_status(self):
        with open(self.ANSIBLE_PULL_LOG_FILE) as pull_log_file:
            pull_log = '\n'.join(pull_log_file.readlines())
            search_term = 'failed='
            fail_index = pull_log.rfind(search_term)
            failed_num = int(pull_log[fail_index + len(search_term)])
            if failed_num == 0:
                self.upgrade_successful = True
            else:
                print failed_num