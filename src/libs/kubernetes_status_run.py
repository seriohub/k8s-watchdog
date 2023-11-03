import asyncio

from utils.config import ConfigK8sProcess
from libs.kubernetes_status import KubernetesStatus
from utils.print_helper import PrintHelper
from utils.handle_error import handle_exceptions_async_method


class KubernetesStatusRun:
    """
    Invoke the state of k8s items cyclically
    """

    def __init__(self,
                 kube_load_method=False,
                 kube_config_file=None,
                 debug_on=True,
                 logger=None,
                 queue=None,
                 cycles_seconds: int = 120,
                 k8s_key_config: ConfigK8sProcess = None):

        self.print_helper = PrintHelper('k8s_status', logger)
        self.print_debug = debug_on

        self.print_helper.debug_if(self.print_debug,
                                   f"__init__")

        self.queue = queue
        forced_cname = None
        if k8s_key_config is not None:
            forced_cname = k8s_key_config.CLUSTER_Name_forced

        self.k8s_stat = KubernetesStatus(kube_load_method,
                                         kube_config_file,
                                         forced_cname,
                                         debug_on,
                                         logger)

        self.cycle_seconds = cycles_seconds
        self.loop = 0

        self.k8s_config = ConfigK8sProcess()
        if k8s_key_config is not None:
            self.k8s_config = k8s_key_config

    @handle_exceptions_async_method
    async def __put_in_queue(self, obj):
        """
        Add object to a queue
        @param obj: data to add in the queue
        """
        self.print_helper.info_if(self.print_debug, "__put_in_queue__")

        await self.queue.put(obj)

    @handle_exceptions_async_method
    async def run(self):
        """
        Main loop
        """
        self.print_helper.info(f"start main procedure seconds {self.cycle_seconds}")

        seconds_waiting = self.cycle_seconds + 1
        index = 0
        list_ns = []
        # add wait
        await asyncio.sleep(2)

        # LS 2023.10.21 add cluster name
        cluster_name = self.k8s_stat.get_cluster_name_loaded()

        data_res = {self.k8s_config.CLUSTER_Name_key: cluster_name}
        await self.__put_in_queue(data_res)

        while True:
            try:
                if seconds_waiting > self.cycle_seconds:
                    if index == 0:
                        self.loop += 1
                        self.print_helper.info(f"start run status. loop counter {self.loop} - index {index}")
                        if self.loop > 500000:
                            self.loop = 1

                    data_res = {}
                    n = 0
                    self.print_helper.info(f"index request {index}-{n}")
                    match index:
                        case 0:
                            # send start data key for capturing the state in one message
                            if self.k8s_config.disp_MSG_key_unique:
                                data_res[self.k8s_config.disp_MSG_key_start] = "start"
                        case 1:
                            # nodelist
                            n = 1
                            if self.k8s_config.NODE_enable:
                                nodelist = self.k8s_stat.get_node_list(only_problem=True)
                                data_res[self.k8s_config.NODE_key] = nodelist

                        case 2:
                            n = 2
                            list_ns = self.k8s_stat.get_namespace()

                            if self.k8s_config.POD_enable:
                                # pod
                                pods_error = self.k8s_stat.get_pods(namespace=list_ns, phase_equal=False)
                                data_res[self.k8s_config.POD_key] = pods_error

                        case 3:
                            n = 3
                            if self.k8s_config.DPL_enable:
                                # deployment sets
                                depl_error = self.k8s_stat.get_deployment(namespace=list_ns,
                                                                          extract_equal0=self.k8s_config.DPL_pods0,
                                                                          extract_not_equal=True)
                                data_res[self.k8s_config.DPL_key] = depl_error
                        case 4:
                            n = 4
                            if self.k8s_config.SS_enable:
                                # stateful sets
                                sts_error = self.k8s_stat.get_stateful_set(namespace=list_ns,
                                                                           extract_equal0=self.k8s_config.SS_pods0,
                                                                           extract_not_equal=True)
                                data_res[self.k8s_config.SS_key] = sts_error
                        case 5:
                            n = 5
                            # replicaset
                            if self.k8s_config.RS_enable:
                                replicaset_error = self.k8s_stat.get_replica_set(namespace=list_ns,
                                                                                 extract_equal0=
                                                                                 self.k8s_config.RS_pods0,
                                                                                 extract_not_equal=True)
                                data_res[self.k8s_config.RS_key] = replicaset_error
                        case 6:
                            n = 6
                            # # daemon sets
                            if self.k8s_config.DS_enable:
                                daemons_set_errors = self.k8s_stat.get_daemon_set(namespace=list_ns,
                                                                                  extract_equal0=
                                                                                  self.k8s_config.DS_pods0,
                                                                                  extract_not_equal=True)
                                data_res[self.k8s_config.DS_key] = daemons_set_errors
                        case 7:
                            n = 7
                            if self.k8s_config.PVC_enable:
                                # persistent volume claims
                                pvc_unbound = self.k8s_stat.get_pvc_claim(namespace=list_ns,
                                                                          equal_to_phase=False)
                                data_res[self.k8s_config.PVC_key] = pvc_unbound
                        case 8:
                            n = 8
                            if self.k8s_config.PV_enable:
                                # PV
                                pv_unbound = self.k8s_stat.get_pv(equal_to_phase=False)
                                data_res[self.k8s_config.PV_key] = pv_unbound
                        case 9:
                            n = 9
                            # send end data key for sending message
                            if self.k8s_config.disp_MSG_key_unique:
                                data_res[self.k8s_config.disp_MSG_key_end] = "end"

                        case _:
                            n = 10
                            seconds_waiting = 0
                            index = 0

                    if seconds_waiting > 0:
                        index += 1
                        if data_res:
                            await self.__put_in_queue(data_res)

                    else:
                        index = 0
                        self.print_helper.info(f"end read.{n}")

                if seconds_waiting % 30 == 0:
                    self.print_helper.info(f"...wait next check in {self.cycle_seconds - seconds_waiting} sec")

                await asyncio.sleep(1)
                seconds_waiting += 1

            except Exception as e:
                self.print_helper.error(f"run.{e}")
            finally:
                self.print_helper.debug_if(self.print_debug, f"run")
                # await asyncio.sleep(20)
