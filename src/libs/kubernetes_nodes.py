from utils.print_helper import PrintHelper
from utils.handle_error import handle_exceptions_method


class KubernetesGetNodes:
    """
    Obtain the list of k8s nodes
    """

    def __init__(self,
                 debug_on=True,
                 logger=None,
                 k8s_api_instance=None,
                 cluster_name=None):

        self.print_helper = PrintHelper('kubernetes_get_nodes', logger)
        self.print_debug = debug_on

        self.print_helper.info_if(self.print_debug,
                                  f"__init__")

        self.api_instance = k8s_api_instance
        self.cluster_name = cluster_name

    @handle_exceptions_method
    def get_node_list(self,
                      only_problem=False):
        """
        Obtain K8S nodes
        :param only_problem:
        :return: List of nodes
        """
        try:
            total_nodes = 0
            retrieved_nodes = 0
            add_node = True
            nodes = {}
            self.print_helper.info(f"get_node_list. only with problem {only_problem}")
            active_context = ''
            # Listing the cluster nodes
            node_list = self.api_instance.list_node()
            for node in node_list.items:
                total_nodes += 1
                node_details = {}

                # api_response = self.api_instance.patch_node(node.metadata.name, body)
                self.print_helper.info_if(self.print_debug,
                                          f"Cluster Nodes: {node.metadata.name}")
                node_details['cluster'] = self.cluster_name
                node_details['context'] = active_context
                node_details['name'] = node.metadata.name
                if 'kubernetes.io/role' in node.metadata.labels:
                    self.print_helper.info_if(self.print_debug,
                                              f"[{node.metadata.name}] "
                                              f"role:{node.metadata.labels['kubernetes.io/role']}")
                    node_details['role'] = node.metadata.labels['kubernetes.io/role']
                else:
                    self.print_helper.info_if(self.print_debug,
                                              f"[{node.metadata.name}] role:control-plane")
                    node_details['role'] = 'control-plane'
                version = node.status.node_info.kube_proxy_version
                node_details['version'] = version
                self.print_helper.info_if(self.print_debug,
                                          f"[{node.metadata.name}] version :{version}")

                node_details['architecture'] = node.status.node_info.architecture
                self.print_helper.info_if(self.print_debug,
                                          f"[{node.metadata.name}] "
                                          f"architecture :{version}")

                node_details['operating_system'] = node.status.node_info.operating_system
                self.print_helper.info_if(self.print_debug,
                                          f"[{node.metadata.name}] "
                                          f"operating_system :{node.status.node_info.operating_system}")

                node_details['kernel_version'] = node.status.node_info.kernel_version
                self.print_helper.info_if(self.print_debug, f"[{node.metadata.name}] "
                                                            f"kernel_version :{node_details['kernel_version']}")

                node_details['os_image'] = node.status.node_info.os_image
                self.print_helper.info_if(self.print_debug, f"[{node.metadata.name}] "
                                                            f"os_image :{node.status.node_info.os_image}")

                node_details['addresses'] = node.status.addresses
                for detail in node.status.addresses:
                    self.print_helper.info_if(self.print_debug,
                                              f"[{node.metadata.name}] ip :{detail.address} type: {detail.type}")

                condition = {}
                for detail in node.status.conditions:
                    condition[detail.reason] = detail.status
                    self.print_helper.info_if(self.print_debug,
                                              f"[{node.metadata.name}] reason:{detail.reason}[{detail.type}]"
                                              f" status: {detail.status}")

                    if only_problem:
                        if add_node:
                            if detail.reason == 'KubeletReady':
                                if not bool(detail.status):
                                    add_node = False
                            else:
                                if bool(detail.status):
                                    add_node = False
                    else:
                        add_node = True
                node_details['conditions'] = condition

                if add_node:
                    retrieved_nodes += 1
                    nodes[node.metadata.name] = node_details

            self.print_helper.info(f"Total nodes {total_nodes}- retrieved {retrieved_nodes}")

            return nodes

        except Exception as err:
            self.print_helper.error_and_exception(f"get_node_list", err)
            return None
