import subprocess
import json
import os


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

    def runs_on_pi3(self):
        if not self.model:
            return False
        elif u'Pi 3' in self.model:
            return True
        else:
            return False

    def pi3_builtin_wifi_only(self):
        if self.runs_on_pi3() and len(self.wifi_devices) == 1:
            return True
        else:
            return False

    def __str__(self):
        return '\n'.join((self.model, str(self.wifi_devices)))


class ModelInfo:

    MODEL_PATH = '/proc/device-tree/model'

    def __init__(self):
        self.model = self.get_model_str()

    def get_model_str(self):
        if not os.path.exists(self.MODEL_PATH):
            return None

        with open(self.MODEL_PATH) as model_file:
            model = model_file.read().strip()
            return model

    def runs_on_pi3(self):
        if not self.model:
            return False
        elif u'Pi 3' in self.model:
            return True
        else:
            return False


class UpdateStatus:

    ANSIBLE_PULL_LOG_FILE = '/var/tmp/log/ansible-pull.log'
    GIT_REPO_LOCAL_DIR = '/var/lib/ansible/local'

    def __init__(self):
        self.branch = None
        self.tag = None
        self.last_commit_short = None
        self.update_utc_time = None
        self.upgrade_successful = False

        self.get_upgrade_status()
        self.get_last_commit_short_hash()
        self.get_update_time()
        self.get_git_branch()
        self.get_git_tag()

    def __str__(self):
        return '\n'.join((str(self.branch), str(self.last_commit_short), str(self.update_utc_time), str(self.upgrade_successful)))

    def get_git_tag(self):
        try:
            self.tag = subprocess.check_output(['/usr/bin/git', '-C', self.GIT_REPO_LOCAL_DIR, 'describe', '--tags']).strip()
        except:
            pass

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

    def get_version(self):
        if self.tag:
            return self.tag
        else:
            return self.branch + '/' + self.last_commit_short

    def get_update_time(self):
        try:
            from os.path import getctime
            from datetime import datetime
            self.update_utc_time = datetime.utcfromtimestamp(getctime(self.ANSIBLE_PULL_LOG_FILE))
        except:
            pass

    def get_upgrade_status(self):
        with open(self.ANSIBLE_PULL_LOG_FILE) as pull_log_file:
            pull_log = '\n'.join(pull_log_file.readlines())
            search_term = 'failed='
            fail_index = pull_log.rfind(search_term)
            failed_num = int(pull_log[fail_index + len(search_term)])
            if failed_num == 0:
                self.upgrade_successful = True
