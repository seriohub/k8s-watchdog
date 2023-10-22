from libs.kubernetes_namespace import KubernetesGetNamespace
import kubernetes
from utils.print_helper import PrintHelper
from utils.handle_error import handle_exceptions_method


class KubernetesGetRps:
    """
    Obtain the list of replica sets in k8s
    """

    def __init__(self,
                 debug_on=True,
                 logger=None,
                 k8s_api_instance=None,
                 k8s_apps_instance=None,
                 cluster_name=None):

        self.print_helper = PrintHelper('kubernetes_get_rps', logger)
        self.print_debug = debug_on

        self.print_helper.info_if(self.print_debug,
                                  f"__init__")
        self.k8s_namespace = KubernetesGetNamespace(debug_on,
                                                    logger,
                                                    k8s_api_instance)
        self.api_instance = k8s_api_instance
        self.apps_instance = k8s_apps_instance

        self.cluster_name = cluster_name

    @handle_exceptions_method
    def get_replica_set(self,
                        namespace,
                        extract_not_equal=False,
                        extract_equal0=False):
        try:
            self.print_helper.info(f"get_replica_set "
                                   f"-not equal: {extract_not_equal} -equal0:{extract_equal0}")
            rt_sets = {}
            if namespace is not None:
                nm_list = namespace
            else:
                nm_list = self.k8s_namespace.get_namespace()
            total = 0
            if nm_list is not None:
                for nm in nm_list:
                    self.print_helper.info_if(self.print_debug,
                                              f"get_replica_set  nm:{nm}")
                    # details = {}

                    nm_dp = self.apps_instance.list_namespaced_replica_set(nm)
                    for st in nm_dp.items:
                        total += 1

                        add_st_sets = False

                        if extract_not_equal or extract_equal0:

                            if ((extract_not_equal
                                 and st.status.available_replicas is not None
                                 and st.status.replicas is not None
                                 and st.status.available_replicas != st.status.replicas)
                                    or (extract_equal0 and (st.status.replicas is None
                                                            or st.status.replicas == 0))):
                                add_st_sets = True
                        else:
                            add_st_sets = True

                        if add_st_sets:
                            self.print_helper.info_if(self.print_debug,
                                                      f"Replica sets:{st.metadata.name} "
                                                      f"in {st.metadata.namespace}")
                            details = {'cluster': self.cluster_name,
                                       'namespace': st.metadata.namespace,
                                       'available_replicas': st.status.available_replicas,
                                       'replicas': st.status.replicas,
                                       'ready_replicas': st.status.ready_replicas}

                            if self.print_debug:
                                self.print_helper.info(f"ReplicaSet.available replicas :"
                                                       f" {st.status.available_replicas}")
                                self.print_helper.info(f"ReplicaSet.replicas :"
                                                       f" {st.status.replicas}")
                                self.print_helper.info(f"ReplicaSet.ready replicas :"
                                                       f" {st.status.ready_replicas}")
                            rt_sets[st.metadata.name] = details

            self.print_helper.info(f"{len(rt_sets)}/{total} ReplicaSet found "
                                   f"{'with problem' if extract_equal0 or extract_not_equal else ''}")

            return rt_sets

        except kubernetes.client.ApiException as e:
            self.print_helper.error(f"get_replica_set k8s error : {e}")
            if e.status == 404:
                return None

            raise e
        except Exception as err:
            # self.print_helper.error(f"get_replica_set error : {err}")
            self.print_helper.error_and_exception(f"get_replica_set", err)
            return None
