import subprocess
import os


class ModelInfo:

    MODEL_PATH = '/proc/device-tree/model'
    WIFI_DEVICE_PATH = '/sys/class/net/wlan0/device/driver/module'
    INTERNAL_KERNEL_MODULE = 'brcmfmac'

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

    def uses_external_wifi(self):
        try:
            link = os.readlink(self.WIFI_DEVICE_PATH)
            return os.path.basename(link) != self.INTERNAL_KERNEL_MODULE
        except (IOError, OSError):
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
        elif all((self.branch, self.last_commit_short)):
            return self.branch + '/' + self.last_commit_short
        else:
            return ''

    def get_update_time(self):
        try:
            from os.path import getctime
            from datetime import datetime
            self.update_utc_time = datetime.utcfromtimestamp(getctime(self.ANSIBLE_PULL_LOG_FILE))
        except:
            pass

    def get_upgrade_status(self):
        try:
            with open(self.ANSIBLE_PULL_LOG_FILE) as pull_log_file:
                pull_log = '\n'.join(pull_log_file.readlines())
                if '"failed": true' not in pull_log:
                    self.upgrade_successful = True
        except:
            pass
