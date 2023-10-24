from libs.kubernetes_namespace import KubernetesGetNamespace
import kubernetes
from utils.print_helper import PrintHelper
from utils.handle_error import handle_exceptions_method


class KubernetesGetDms:
    """
    Obtain the list of the daemon sets from k8s API
    """

    def __init__(self,
                 debug_on=True,
                 logger=None,
                 k8s_api_instance=None,
                 k8s_apps_instance=None,
                 cluster_name=None):

        self.print_helper = PrintHelper('kubernetes_get_dms',
                                        logger)
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
    def get_daemon_set(self,
                       namespace,
                       extract_not_equal=False,
                       extract_equal0=False):
        try:
            self.print_helper.info(f"get_daemon_set "
                                   f"-not equal: {extract_not_equal} -equal0:{extract_equal0}")
            dm_sets = {}
            if namespace is not None:
                nm_list = namespace
            else:
                nm_list = self.k8s_namespace.get_namespace()
            total = 0
            if nm_list is not None:
                for nm in nm_list:
                    self.print_helper.info_if(self.print_debug,
                                              f"get_daemon_set  nm:{nm}")
                    nm_dp = self.apps_instance.list_namespaced_daemon_set(nm)
                    for st in nm_dp.items:
                        total += 1

                        add_st_sets = False
                        if extract_not_equal or extract_equal0:

                            if ((extract_not_equal
                                 and st.status.number_available is not None
                                 and st.status.number_ready is not None
                                 and st.status.number_available != st.status.number_ready)
                                    or (extract_equal0 and (st.status.number_ready is None
                                                            or st.status.number_ready == 0))):
                                add_st_sets = True
                        else:
                            add_st_sets = True

                        if add_st_sets:
                            self.print_helper.info_if(self.print_debug,
                                                      f"DaemonSet:{st.metadata.name} in {st.metadata.namespace}")
                            details = {'cluster': self.cluster_name,
                                       'namespace': st.metadata.namespace,
                                       'current_number_scheduled': st.status.current_number_scheduled,
                                       'desired_number_scheduled': st.status.desired_number_scheduled,
                                       'number_available': st.status.number_available,
                                       'updated_number_scheduled': st.status.updated_number_scheduled,
                                       'number_ready': st.status.number_ready
                                       }

                            if self.print_debug:
                                self.print_helper.info(f"DaemonSet.current_number_scheduled : "
                                                       f"{st.status.current_number_scheduled}")
                                self.print_helper.info(f"DaemonSet.desired_number_scheduled :"
                                                       f" {st.status.desired_number_scheduled}")
                                self.print_helper.info(f"DaemonSet.number_ready : {st.status.number_ready}")
                                self.print_helper.info(f"DaemonSet.number_miss-scheduled :"
                                                       f" {st.status.number_misscheduled}")
                                self.print_helper.info(f"DaemonSet.updated_number_scheduled :"
                                                       f" {st.status.updated_number_scheduled}")

                            dm_sets[st.metadata.name] = details

            self.print_helper.info(f"{len(dm_sets)}/{total} get_daemon_set found "
                                   f"{'with problem' if extract_equal0 or extract_not_equal else ''}")

            return dm_sets

        except kubernetes.client.ApiException as e:
            self.print_helper.error(f"get_daemon_set k8s error : {e}")
            if e.status == 404:
                return None

            raise e
        except Exception as err:
            # self.print_helper.error(f"get_daemon_set error : {err}")
            self.print_helper.error_and_exception(f"get_daemon_set", err)
            return None
