import os

from kubernetes import client, config
from utils.print_helper import PrintHelper
from libs.kubernetes_nodes import KubernetesGetNodes
from libs.kubernetes_namespace import KubernetesGetNamespace
from libs.kubernetes_pods import KubernetesGetPods
from libs.kubernetes_statefulset import KubernetesGetSfs
from libs.kubernetes_replicaset import KubernetesGetRps
from libs.kubernetes_deployment import KubernetesGetDeployment
from libs.kubernetes_daemonset import KubernetesGetDms
from libs.kubernetes_pv_pvc import KubernetesGetPvPvc


class KubernetesStatus:
    """
    Class for updating the state of k8s items over API
    """

    def __init__(self,
                 kube_config_load_method=False,
                 kube_config_file=None,
                 debug_on=True,
                 logger=None):

        self.print_helper = PrintHelper('k8s_status', logger)
        self.print_debug = debug_on

        self.print_helper.info_if(self.print_debug,
                                  f"__init__")
        load_default = True
        if kube_config_file is not None:
            if len(kube_config_file) > 0:
                self.print_helper.info_if(self.print_debug,
                                          f"config file {kube_config_file}")

                if os.path.isfile(kube_config_file):
                    load_default = False
                    config.load_kube_config(config_file=kube_config_file)
                else:
                    load_default = True
                    self.print_helper.error(f"config file"
                                            f"is not a valid file. Load default")

        if load_default:
            if kube_config_load_method:
                self.print_helper.info_if(self.print_debug,
                                          f"load_kube_config")
                config.load_kube_config()
            else:
                self.print_helper.info_if(self.print_debug,
                                          f"load_incluster_config")

                config.load_incluster_config()

        self.api_instance = client.CoreV1Api()
        self.apps_instance = client.AppsV1Api()

        self.k8s_nodes = KubernetesGetNodes(debug_on, logger, self.api_instance)
        self.k8s_namespace = KubernetesGetNamespace(debug_on, logger, self.api_instance)
        self.k8s_pods = KubernetesGetPods(debug_on, logger, self.api_instance, self.apps_instance)
        self.k8s_sfs = KubernetesGetSfs(debug_on, logger, self.api_instance, self.apps_instance)
        self.k8s_rps = KubernetesGetRps(debug_on, logger, self.api_instance, self.apps_instance)
        self.k8s_deployment = KubernetesGetDeployment(debug_on, logger, self.api_instance, self.apps_instance)
        self.k8s_dms = KubernetesGetDms(debug_on, logger, self.api_instance, self.apps_instance)
        self.k8s_pv_c = KubernetesGetPvPvc(debug_on, logger, self.api_instance)

    def get_node_list(self, only_problem=False):
        return self.k8s_nodes.get_node_list(only_problem)

    def get_namespace(self):
        return self.k8s_namespace.get_namespace()

    def get_pods(self,
                 namespace,
                 label_selector: str = '',
                 phase: str = 'Running',
                 phase_equal=False):

        return self.k8s_pods.get_pods(namespace,
                                      label_selector,
                                      phase,
                                      phase_equal)

    def get_stateful_set(self, namespace,
                         extract_not_equal=False,
                         extract_equal0=False):

        return self.k8s_sfs.get_stateful_set(namespace,
                                             extract_not_equal,
                                             extract_equal0)

    def get_replica_set(self,
                        namespace,
                        extract_not_equal=False,
                        extract_equal0=False):

        return self.k8s_rps.get_replica_set(namespace,
                                            extract_not_equal,
                                            extract_equal0)

    def get_deployment(self,
                       namespace,
                       extract_not_equal=False,
                       extract_equal0=False):

        return self.k8s_deployment.get_deployment(namespace,
                                                  extract_not_equal,
                                                  extract_equal0)

    def get_daemon_set(self,
                       namespace,
                       extract_not_equal=False,
                       extract_equal0=False):

        return self.k8s_dms.get_daemon_set(namespace,
                                           extract_not_equal,
                                           extract_equal0)

    def get_pvc_claim(self,
                      namespace,
                      phase: str = 'Bound',
                      equal_to_phase=False):
        return self.k8s_pv_c.get_pvc_claim(namespace,
                                           phase,
                                           equal_to_phase)

    def get_pv(self,
               phase: str = 'Bound',
               equal_to_phase=False):
        return self.k8s_pv_c.get_pv(phase, equal_to_phase)
