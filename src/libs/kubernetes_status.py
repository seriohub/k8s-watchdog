import os


from kubernetes import client
from kubernetes import config
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
                    load_default = False   # Forced to else
                    self.print_helper.error(f"config file"
                                            f"is not a valid file. Load default")

        if load_default:
            if kube_config_load_method:
                self.print_helper.info_if(self.print_debug,
                                          f"load_kube_config- out-of-the-cluster")
                config.load_kube_config()
            else:
                self.print_helper.info_if(self.print_debug,
                                          f"load in-cluster configuration  ")

                config.load_incluster_config()

        self.k8s_in_cluster = not kube_config_load_method
        self.k8s_config_file = kube_config_file

        self.api_instance = client.CoreV1Api()
        self.apps_instance = client.AppsV1Api()
        # Load cluster name
        self.cluster_name = self.get_cluster_name()

        self.k8s_nodes = KubernetesGetNodes(debug_on,
                                            logger,
                                            self.api_instance,
                                            cluster_name=self.cluster_name)
        self.k8s_namespace = KubernetesGetNamespace(debug_on,
                                                    logger,
                                                    self.api_instance)
        self.k8s_pods = KubernetesGetPods(debug_on,
                                          logger,
                                          self.api_instance,
                                          self.apps_instance,
                                          cluster_name=self.cluster_name)
        self.k8s_sfs = KubernetesGetSfs(debug_on,
                                        logger,
                                        self.api_instance,
                                        self.apps_instance,
                                        cluster_name=self.cluster_name)
        self.k8s_rps = KubernetesGetRps(debug_on,
                                        logger,
                                        self.api_instance,
                                        self.apps_instance,
                                        cluster_name=self.cluster_name)
        self.k8s_deployment = KubernetesGetDeployment(debug_on,
                                                      logger,
                                                      self.api_instance,
                                                      self.apps_instance,
                                                      cluster_name=self.cluster_name)
        self.k8s_dms = KubernetesGetDms(debug_on,
                                        logger,
                                        self.api_instance,
                                        self.apps_instance,
                                        cluster_name=self.cluster_name)
        self.k8s_pv_c = KubernetesGetPvPvc(debug_on,
                                           logger,
                                           self.api_instance,
                                           cluster_name=self.cluster_name)

    def get_cluster_name_from_config_file(self):
        try:
            cluster_name = None
            if not self.k8s_in_cluster:
                self.print_helper.info(f"get_cluster_name_from_config_file {self.k8s_config_file}")

                cluster_context = config.kube_config.list_kube_config_contexts(config_file=self.k8s_config_file)
                self.print_helper.info_if(self.print_debug,
                                          f"get_cluster_name:context {cluster_context}")
                cluster_name = cluster_context[1]['context']['cluster']
                self.print_helper.info(f"cluster name from file  {cluster_name}")

            return cluster_name
        except Exception as err:
            self.print_helper.error_and_exception(f"get_cluster_name_from_config_file", err)
            return None

    def get_cluster_name_from_in_cluster_config(self):
        try:
            cluster_name = None
            if self.k8s_in_cluster:
                current_context = config.list_kube_config_contexts()[1]
                # The second element contains the current context

                if current_context:
                    cluster_name = current_context.get('context').get('cluster')

            return cluster_name
        except Exception as err:
            self.print_helper.error_and_exception(f"get_cluster_name_from_in_cluster_config", err)
            return None

    def get_cluster_name(self):
        cluster_name = "Unknown"
        try:
            self.print_helper.info(f"get_cluster_name")

            # cluster_context = config.kube_config.list_kube_config_contexts()
            # self.print_helper.info_if(self.print_debug,
            #                           f"get_cluster_name:context {cluster_context}")
            # cluster_name = cluster_context[1]['context']['cluster']
            # self.print_helper.info_if(self.print_debug,
            #                           f"get_cluster_name:cluster name  {cluster_name}")
            # self.cluster_name = cluster_name

            cluster_name = self.get_cluster_name_from_config_file()

            if cluster_name is None:
                cluster_name = self.get_cluster_name_from_in_cluster_config()

            if cluster_name is None:
                # Retrieve information about the current cluster
                cluster_info = self.api_instance.read_namespaced_config_map("kube-root-ca.crt",
                                                                            "kube-system")

                # Extract the cluster name from the ConfigMap data
                cluster_name = cluster_info.data.get("cluster-name", "Unknown")

        except Exception as err:
            self.print_helper.error_and_exception(f"get_cluster_name", err)
            cluster_name = "Unknown"
        finally:
            self.cluster_name = cluster_name
            return cluster_name

    def get_cluster_name_loaded(self):
        self.print_helper.info(f"get_cluster_name_loaded {self.cluster_name}")
        return self.cluster_name

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
        return self.k8s_pv_c.get_pv(phase,
                                    equal_to_phase)
