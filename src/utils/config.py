from dotenv import load_dotenv
import os
from utils.handle_error import handle_exceptions_static_method, handle_exceptions_method


# class syntax
class ConfigProgram:
    def __init__(self, path_env=None):
        res = load_dotenv(dotenv_path=path_env)
        print(f"INFO    [Env] Load env={res}")

    @staticmethod
    @handle_exceptions_static_method
    def load_key(key, default, print_out: bool = True, mask_value: bool = False):
        value = os.getenv(key)
        if print_out:
            if mask_value and len(value) > 2:
                index = int(len(value) / 2)
                partial = '*' * index
                print(f"INFO    [Env] load_key.key={key} value={value[:index]}{partial}")
            else:
                print(f"INFO    [Env] load_key.key={key} value={value}")
        if value is None or \
                len(value) == 0:
            value = default
        return value

    @handle_exceptions_method
    def logger_key(self):
        return self.load_key('LOG_KEY', 'k8s-wdt')

    @handle_exceptions_method
    def logger_msg_format(self):
        default = '%(asctime)s :: [%(levelname)s] :: %(message)s'
        return self.load_key('LOG_FORMAT', default)

    @handle_exceptions_method
    def logger_save_to_file(self):
        res = self.load_key('LOG_SAVE', 'False')
        return True if res.upper() == 'TRUE' else False

    @handle_exceptions_method
    def logger_folder(self):
        return self.load_key('LOG_DEST_FOLDER',
                             './logs')

    @handle_exceptions_method
    def logger_filename(self):
        return self.load_key('LOG_FILENAME',
                             'k8s.log')

    @handle_exceptions_method
    def logger_max_filesize(self):
        return int(self.load_key('LOG_MAX_FILE_SIZE',
                                 4000000))

    @handle_exceptions_method
    def logger_his_backups_files(self):
        return int(self.load_key('LOG_FILES_BACKUP',
                                 '5'))

    @handle_exceptions_method
    def logger_level(self):
        return int(self.load_key('LOG_LEVEL',
                                 '20'))

    @handle_exceptions_method
    def process_run_sec(self):
        res = self.load_key('PROCESS_CYCLE_SEC',
                            '120')

        if len(res) == 0:
            res = '120'
        return int(res)

    @handle_exceptions_method
    def internal_debug_enable(self):
        res = self.load_key('DEBUG', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def telegram_token(self):
        return self.load_key('TELEGRAM_TOKEN', '', mask_value=True)

    @handle_exceptions_method
    def telegram_chat_id(self):
        return self.load_key('TELEGRAM_CHAT_ID', '', mask_value=True)

    @handle_exceptions_method
    def telegram_enable(self):
        res = self.load_key('TELEGRAM_ENABLE', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def telegram_max_msg_len(self):
        res = self.load_key('TELEGRAM_MAX_MSG_LEN',
                            '2000')

        if len(res) == 0:
            res = '2000'
        return int(res)

    @handle_exceptions_method
    def telegram_rate_limit_minute(self):
        res = self.load_key('TELEGRAM_MAX_MSG_MINUTE',
                            '20')

        if len(res) == 0:
            res = '20'
        return int(res)

    @handle_exceptions_method
    def telegram_alive_message_hours(self):
        res = self.load_key('TELEGRAM_ALIVE_MSG_HOURS',
                            '24')
        n_hours = int(res)
        if n_hours < 0:
            n_hours = 0
        elif n_hours > 100:
            n_hours = 100

        return n_hours

    @handle_exceptions_method
    def k8s_load_kube_config_method(self):
        res = self.load_key('PROCESS_LOAD_KUBE_CONFIG', 'True')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def k8s_config_file(self):
        return self.load_key('PROCESS_KUBE_CONFIG', None)

    @handle_exceptions_method
    def k8s_nodes_enable(self):
        res = self.load_key('K8S_NODE', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def k8s_pods_enable(self):
        res = self.load_key('K8S_PODS', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def k8s_deployment_enable(self):
        res = self.load_key('K8S_DEPLOYMENT', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def k8s_deployment_pods0(self):
        res = self.load_key('K8S_DEPLOYMENT_P0', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def k8s_stateful_sets_enable(self):
        res = self.load_key('K8S_STATEFUL_SETS', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def k8s_stateful_sets_pods0(self):
        res = self.load_key('K8S_STATEFUL_SETS_P0', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def k8s_replica_sets_enable(self):
        res = self.load_key('K8S_REPLICA_SETS', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def k8s_replica_sets_pods0(self):
        res = self.load_key('K8S_REPLICA_SETS_P0', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def k8s_daemons_sets_enable(self):
        res = self.load_key('K8S_DAEMON_SETS', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def k8s_daemons_sets_pods0(self):
        res = self.load_key('K8S_DAEMON_SETS_P0', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def k8s_pvc_enable(self):
        res = self.load_key('K8S_PVC', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False

    @handle_exceptions_method
    def k8s_pv_enable(self):
        res = self.load_key('K8S_PV', 'False')
        return True if res.lower() == "true" or res.lower() == "1" else False


class ConfigK8sProcess:
    def __init__(self):
        self.POD_enable = True
        self.POD_key = 'pods'

        self.SS_enable = True
        self.SS_pods0 = False
        self.SS_key = 'stateful_sets'

        self.RS_enable = True
        self.RS_pods0 = False
        self.RS_key = 'replicaset_sets'

        self.DS_enable = True
        self.DS_pods0 = True
        self.DS_key = 'daemon_sets'

        self.PVC_enable = True
        self.PVC_key = 'pvc'

        self.PV_enable = True
        self.PV_key = 'pv'

        self.DPL_enable = True
        self.DPL_pods0 = False
        self.DPL_key = 'deployment'

        self.NODE_enable = True
        self.NODE_key = 'nodelist'
