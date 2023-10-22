from libs.kubernetes_namespace import KubernetesGetNamespace
import kubernetes
from utils.print_helper import PrintHelper
from utils.handle_error import handle_exceptions_method


class KubernetesGetPvPvc:
    """
    Obtain the list of pv or pvc defined in k8s
    """

    def __init__(self,
                 debug_on=True,
                 logger=None,
                 k8s_api_instance=None,
                 cluster_name=None):

        self.print_helper = PrintHelper('kubernetes_get_pv_pvc', logger)
        self.print_debug = debug_on

        self.print_helper.info_if(self.print_debug,
                                  f"__init__")
        self.k8s_namespace = KubernetesGetNamespace(debug_on, logger)
        self.api_instance = k8s_api_instance
        self.cluster_name = cluster_name

    @handle_exceptions_method
    def get_pvc_claim(self,
                      namespace,
                      phase: str = 'Bound',
                      equal_to_phase=False):
        try:
            self.print_helper.info(f"get_pvc_claim -phase: {phase} -equal:{equal_to_phase}")
            st_sets = {}

            if namespace is not None:
                nm_list = namespace
            else:
                nm_list = self.k8s_namespace.get_namespace(self.api_instance)
            total = 0
            if nm_list is not None:
                for nm in nm_list:
                    self.print_helper.info_if(self.print_debug,
                                              f"get_pvc_claim  nm:{nm}")
                    nm_dp = self.api_instance.list_namespaced_persistent_volume_claim(nm)
                    for st in nm_dp.items:
                        total += 1

                        add_st_sets = False
                        if phase:
                            if equal_to_phase:
                                if st.status.phase == phase:
                                    add_st_sets = True
                            else:
                                if st.status.phase != phase:
                                    add_st_sets = True
                        else:
                            add_st_sets = True

                        if add_st_sets:
                            self.print_helper.info_if(self.print_debug,
                                                      f"pvc:{st.metadata.name} in {st.metadata.namespace} phase "
                                                      f"{st.status.phase}")
                            details = {'cluster': self.cluster_name,
                                       'namespace': st.metadata.namespace,
                                       'phase': st.status.phase,
                                       'storage_class_name': st.spec.storage_class_name}

                            self.print_helper.info_if(self.print_debug,
                                                      f"pvc.phase : {st.status.phase}")
                            self.print_helper.info_if(self.print_debug,
                                                      f"pvc.storage_class_name: {st.spec.storage_class_name}")
                            st_sets[st.metadata.name] = details

            self.print_helper.info(f"{len(st_sets)}/{total} pvc found "
                                   f"{'in' if equal_to_phase else 'not in'} phase {phase}")

            return st_sets

        except kubernetes.client.ApiException as e:
            self.print_helper.error(f"get_pvc_claim k8s error : {e}")
            if e.status == 404:
                return None

            raise e
        except Exception as err:
            # self.print_helper.error(f"get_pvc_claim error : {err}")
            self.print_helper.error_and_exception(f"get_pvc_claim", err)
            return None

    @handle_exceptions_method
    def get_pv(self,
               phase: str = 'Bound',
               equal_to_phase=False):
        try:
            self.print_helper.info(f"get_pv -phase: {phase} -equal:{equal_to_phase}")

            st_sets = {}
            total = 0
            # if nm_list is not None:
            #     for nm in nm_list:
            nm_dp = self.api_instance.list_persistent_volume()
            for st in nm_dp.items:
                total += 1
                add_st_sets = False
                if phase:
                    if equal_to_phase:
                        if st.status.phase == phase:
                            add_st_sets = True
                    else:
                        if st.status.phase != phase:
                            add_st_sets = True
                else:
                    add_st_sets = True

                if add_st_sets:
                    self.print_helper.info_if(self.print_debug,
                                              f"pv:{st.metadata.name} in {st.metadata.namespace} phase "
                                              f"{st.status.phase}")
                    details = {'cluster': self.cluster_name,
                               'namespace': st.metadata.namespace,
                               'phase': st.status.phase,
                               'storage_class_name': st.spec.storage_class_name,
                               'pv.claim_ref': st.spec.claim_ref.name,
                               'pv.claim_ref_namespace': st.spec.claim_ref.namespace
                               }

                    self.print_helper.info_if(self.print_debug,
                                              f"pv.phase : {st.status.phase}")
                    self.print_helper.info_if(self.print_debug,
                                              f"pv.storage_class_name: {st.spec.storage_class_name}")
                    if st.spec.claim_ref.name is not None:
                        self.print_helper.info_if(self.print_debug,
                                                  f"pv.claim-pvc: {st.spec.claim_ref.name}")
                        self.print_helper.info_if(self.print_debug,
                                                  f"pv.claim-nm: {st.spec.claim_ref.namespace}")
                    st_sets[st.metadata.name] = details

            self.print_helper.info(f"{len(st_sets)}/{total} pv found "
                                   f"{'in' if equal_to_phase else 'not in'} phase {phase}")

            return st_sets

        except kubernetes.client.ApiException as e:
            self.print_helper.error(f"get_pv k8s error : {e}")
            if e.status == 404:
                return None

            raise e
        except Exception as err:
            # self.print_helper.error(f"get_pv error : {err}")
            self.print_helper.error_and_exception(f"get_pv", err)
            return None
