from libs.kubernetes_namespace import KubernetesGetNamespace
import kubernetes
from utils.print_helper import PrintHelper
from utils.handle_error import handle_exceptions_method


class KubernetesGetPods:
    """
    Obtain the list of pods defined in k8s
    """

    def __init__(self,
                 debug_on=True,
                 logger=None,
                 k8s_api_instance=None,
                 k8s_apps_instance=None,
                 cluster_name=None):

        self.print_helper = PrintHelper('kubernetes_get_pods', logger)
        self.print_debug = debug_on

        self.print_helper.info_if(self.print_debug,
                                  f"__init__")
        self.k8s_namespace = KubernetesGetNamespace(debug_on,
                                                    logger,
                                                    k8s_api_instance)
        self.api_instance = k8s_api_instance
        self.apps_instance = k8s_apps_instance
        self.cluster_name = cluster_name

    def set_cluster_name(self, cluster_name):
        self.cluster_name = cluster_name

    @handle_exceptions_method
    def get_pods(self,
                 namespace,
                 label_selector: str = '',
                 phase=None,
                 phase_equal=False):
        """
         Obtain the list of k8s pods created
        :param namespace:
        :param label_selector:
        :param phase: dict of phase to be controlled
        :param phase_equal:
        :return:  List of pods
        """
        namespace = ['matomo']
        # LS 2023.10.28 update the parameter from str to object
        if phase is None or len(phase) == 0:
            phase = {"Running", "Succeeded"}

        try:
            self.print_helper.info(f"get_pods - found pods where phase is  {phase}  and equal {phase_equal} ")
            total_nm = 0
            pods = {}

            if namespace is not None:
                nm_list = namespace
            else:
                nm_list = self.k8s_namespace.get_namespace()

            for nm in nm_list:
                total_nm += 1

                self.print_helper.info_if(self.print_debug, f"get_pods  nm:{nm}")
                if label_selector:
                    nm_list = self.api_instance.list_namespaced_pod(namespace=nm,
                                                                    watch=False,
                                                                    label_selector=label_selector)
                else:
                    nm_list = self.api_instance.list_namespaced_pod(namespace=nm,
                                                                    watch=False)

                if not nm_list.items:
                    self.print_helper.info_if(self.print_debug,
                                              f"no pod '{label_selector}' were found in {nm}'")
                else:
                    self.print_helper.info_if(self.print_debug,
                                              f"Found {len(nm_list.items)} pods in {nm}")

                for pod in nm_list.items:
                    condition = {}
                    self.print_helper.info_if(self.print_debug,
                                              f"pod {pod.metadata.name} is in phase {phase}")
                    add_phase = False
                    if len(phase) > 0:
                        if phase_equal:
                            # if pod.status.phase == phase:
                            if pod.status.phase in phase:
                                add_phase = True
                        else:
                            # if pod.status.phase != phase:
                            if not (pod.status.phase in phase):
                                add_phase = True
                    else:
                        add_phase = True
                    condition['cluster'] = self.cluster_name
                    condition['namespace'] = pod.metadata.namespace
                    condition['phase'] = pod.status.phase

                    n_condition = 0
                    for detail in pod.status.conditions:
                        condition[f'condition_{n_condition}'] = {'message': detail.message,
                                                                 'reason': detail.reason,
                                                                 'status': detail.status,
                                                                 'type': detail.type}
                        n_condition += 1
                        self.print_helper.info_if(self.print_debug,
                                                  f"[{pod.metadata.name}] "
                                                  f"reason:{detail.reason} "
                                                  f"type:{detail.type} "
                                                  f"message:{detail.message} "
                                                  f"status: {detail.status}")

                    if pod.status.container_statuses:
                        # LS  2023.10.18 Comment and iterate each child nodes
                        # condition['cs_restart_count'] = pod.status.container_statuses[0].restart_count
                        # condition['cs_ready'] = pod.status.container_statuses[0].ready
                        # condition['cs_started'] = pod.status.container_statuses[0].started
                        # condition['cs_state'] = pod.status.container_statuses[0].state

                        container_statuses = 0
                        for detail in pod.status.container_statuses:
                            state = "Unknown"
                            if detail.state.waiting is not None:
                                state = "Waiting"
                            elif detail.state.terminated is not None:
                                state = detail.state.terminated.reason
                            elif detail.state.running is not None:
                                state = "Running"

                            condition[f'cs_{container_statuses}'] = {'restart': detail.restart_count,
                                                                     'ready': detail.ready,
                                                                     'started': detail.started,
                                                                     'state': state}

                            self.print_helper.info_if(self.print_debug,
                                                      f"[{pod.metadata.name}] "
                                                      f"restart:{detail.restart_count} "
                                                      f"ready:{detail.ready} "
                                                      f"started:{detail.started} "
                                                      f"state: {state}")

                    if pod.metadata.owner_references:
                        condition['own_controller'] = pod.metadata.owner_references[0].controller
                        condition['own_kind'] = pod.metadata.owner_references[0].kind
                        condition['own_name'] = pod.metadata.owner_references[0].name

                    if add_phase:
                        pods[pod.metadata.name] = condition

            self.print_helper.info(f"{len(pods)} pods found in {total_nm} namespaces "
                                   f"{'' if phase_equal else 'not'} in {phase} phase")

            return pods

        except kubernetes.client.ApiException as e:
            self.print_helper.error(f"error k8s error : {e}")
            if e.status == 404:
                return None
            raise e

        except Exception as err:
            # self.print_helper.error(f"get_pods error : {err}")
            self.print_helper.error_and_exception(f"get_pods", err)
            return None
