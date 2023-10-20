from utils.print_helper import PrintHelper
from utils.handle_error import handle_exceptions_method


class KubernetesGetNamespace:
    """
    Obtain the list of the namespace in k8s
    """

    def __init__(self,
                 debug_on=True,
                 logger=None,
                 k8s_api_instance=None):

        self.print_helper = PrintHelper('kubernetes_get_namespace', logger)
        self.print_debug = debug_on

        self.print_helper.info_if(self.print_debug,
                                  f"__init__")
        self.api_instance = k8s_api_instance

    @handle_exceptions_method
    def get_namespace(self):
        """
        Obtain the list of k8s declared namespaces
        :return: List of namespaces
        """
        try:
            self.print_helper.info(f"get_namespace")
            total_nm = 0
            namespaces = {}
            nm_list = self.api_instance.list_namespace()
            for namespace in nm_list.items:
                total_nm += 1
                # api_response = self.api_instance.patch_namespace(namespace.metadata.name, body)
                # print(namespace)
                details = {'Status': namespace.status}
                namespaces[namespace.metadata.name] = details

            self.print_helper.info(f"namespace found {namespaces.items().__len__()}")

            return namespaces
        except Exception as err:
            # self.print_helper.error(f"get_node_list error : {err}")
            self.print_helper.error_and_exception(f"get_namespace", err)
            return None
