import calendar
from datetime import datetime

from utils.config import ConfigK8sProcess
from utils.print_helper import PrintHelper
from utils.handle_error import handle_exceptions_async_method


class KubernetesChecker:
    """
    The class allows to process the data received from k8s APIs
    """

    def __init__(self,
                 debug_on=True,
                 logger=None,
                 queue=None,
                 telegram_queue=None,
                 telegram_max_msg_len=2000,
                 telegram_alive_message_hours=0,
                 k8s_key_config: ConfigK8sProcess = None):

        self.print_helper = PrintHelper('k8s_checker', logger)
        self.print_debug = debug_on

        self.print_helper.debug_if(self.print_debug,
                                   f"__init__")

        self.queue = queue

        self.telegram_max_msg_len = telegram_max_msg_len
        self.telegram_queue = telegram_queue

        self.k8s_config = ConfigK8sProcess()
        if k8s_key_config is not None:
            self.k8s_config = k8s_key_config

        self.old_node_status = {}
        self.old_pods = {}
        self.old_stateful_set = {}
        self.old_replica_set = {}
        self.old_daemon_set = {}
        self.old_pvc = {}
        self.old_pv = {}
        self.old_deployment = {}

        self.alive_message_seconds = telegram_alive_message_hours * 3600
        self.last_send = calendar.timegm(datetime.today().timetuple())

    @handle_exceptions_async_method
    async def __put_in_queue__(self,
                               queue,
                               obj):
        """
        Add new element to the queue
        :param queue:
        :param obj:
        """
        self.print_helper.info_if(self.print_debug, "__put_in_queue__")

        await queue.put(obj)

    @handle_exceptions_async_method
    async def send_to_telegram(self, message):
        """
        Send message to Telegram engine
        :param message:
        """
        self.print_helper.info(f"send_to_telegram")
        self.last_send = calendar.timegm(datetime.today().timetuple())
        await self.__put_in_queue__(self.telegram_queue,
                                    message)

    @handle_exceptions_async_method
    async def __process_key__(self,
                              data,
                              old_data,
                              enable_keys,
                              title,
                              resolved: bool = False):
        """
         Process k8s elements (extracted from API), compared data with old data
         and push new msg in a queue if required
        :param data: received data
        :param old_data: second-to-last data received
        :param enable_keys: keys dict to process for creating the message
        :param title: title of k8s element (e.g. Pods, Replica Sets...)
        """
        try:
            self.print_helper.info(f"__process_key__")

            # compare new data with old data
            if old_data == data:
                self.print_helper.info(f"{title} new data is equal to old data. skip all")
            else:

                data_keys = data.keys()

                base_title = f'{title} details:\n'
                msg = base_title

                for key_dict in data_keys:
                    process = True
                    self.print_helper.info_if(self.print_debug,
                                              f"{title} name {key_dict}")
                    current_node = data[key_dict]

                    # if key exits in previous data dict
                    if old_data:
                        if key_dict in old_data.keys():
                            if old_data[key_dict] == current_node:
                                self.print_helper.info_if(self.print_debug, f"{title} old data for {key_dict}  "
                                                                            f"is equal to new data. No message")
                                process = False
                    if process:
                        # msg = f'{title} detail\n'
                        msg += f"----------\n"
                        msg += f"Name= {key_dict}\n"
                        print(f"current_node:{current_node}")
                        for key, value in current_node.items():
                            key_value = True
                            if (enable_keys is None or
                                    key in enable_keys):
                                if isinstance(value, dict):
                                    key_value = False
                                    msg += f"{key.title()}:\n"
                                    for key_n, value_n in value.items():
                                        if value_n is not None and len(value_n) > 0:
                                            msg += f"   {key_n.title()}= {value_n}\n"
                            else:
                                key_value = False

                            if key_value:
                                if (value is not None
                                        and len(str(value)) > 0):
                                    msg += f"{key}= {value}\n"

                        # if resolved:
                        #     msg += f"Resolved= True\n"

                        if len(msg) >= self.telegram_max_msg_len:
                            self.print_helper.info_if(self.print_debug,
                                                      f"Max message length reached, force send message")
                            await self.send_to_telegram(msg)
                            # Reset msg len
                            msg = base_title

                    else:
                        self.print_helper.info_if(self.print_debug,
                                                  f"{title} set {key_dict} already status sent")

                if len(msg) > len(base_title):
                    self.print_helper.info_if(self.print_debug, f"Flush last message")

                    await self.send_to_telegram(msg)

                if (not resolved
                        and data is not None
                        and old_data is not None
                        and len(old_data) > 0):
                    # process the old data and find which are solved
                    self.print_helper.info(f"process solved items for {title}")
                    # the namespace is the only key in resolved items
                    await self.__process_key__(data=old_data,
                                               old_data=data,
                                               enable_keys=['namespace'],
                                               title=f"Resolved {title}",
                                               resolved=True)

        except Exception as err:
            self.print_helper.error_and_exception(f"__process_key__{title}", err)

    @handle_exceptions_async_method
    async def __unpack_data__(self, data):
        """
         Check the key received and calls the procedure associated with the key type
        :param data:
        """
        self.print_helper.debug_if("__unpack_data")
        try:
            if isinstance(data, dict):
                if self.k8s_config.CLUSTER_Name_key in data:
                    await self.__process_cluster_name__(data)
                elif self.k8s_config.NODE_key in data:
                    await self.__process_nodes__(data)
                elif self.k8s_config.POD_key in data:
                    await self.__process_pods__(data)
                elif self.k8s_config.SS_key in data:
                    await self.__process_stateful_sets__(data)
                elif self.k8s_config.RS_key in data:
                    await self.__process_replica_sets__(data)
                elif self.k8s_config.DS_key in data:
                    await self.__process_daemon_sets__(data)
                elif self.k8s_config.DPL_key in data:
                    await self.__process_deployment__(data)
                elif self.k8s_config.PV_key in data:
                    await self.__process_pv__(data)
                elif self.k8s_config.PVC_key in data:
                    await self.__process_pvc__(data)
                else:
                    self.print_helper.info(f"key not defined")
            else:
                self.print_helper.info(f"__unpack_data.the message is not a type of dict")

            # telegram alive message
            if self.alive_message_seconds > 0:
                diff = calendar.timegm(datetime.today().timetuple()) - self.last_send
                if diff > self.alive_message_seconds:
                    self.print_helper.info(f"__unpack_data.send alive message")
                    await self.send_to_telegram("The system is running. No warning/errors on k8s")

        except Exception as err:
            self.print_helper.error_and_exception(f"__unpack_data", err)

    @handle_exceptions_async_method
    async def __process_nodes__(self, data):
        """
        Data type Cluster nodes
        :param data:
        """

        self.print_helper.info_if(self.print_debug, f"Node status received")
        nodes_status = data[self.k8s_config.NODE_key]

        enable_keys = ['context',
                       'name',
                       'role',
                       'version',
                       'conditions']
        await self.__process_key__(data=nodes_status,
                                   old_data=self.old_node_status,
                                   enable_keys=enable_keys,
                                   title='Node')
        self.old_node_status = nodes_status

    @handle_exceptions_async_method
    async def __process_cluster_name__(self, data):
        self.print_helper.info(f"__process_cluster_name__")

        nodes_name = data[self.k8s_config.CLUSTER_Name_key]

        self.print_helper.info(f"cluster name {nodes_name}")
        if nodes_name is not None:
            self.print_helper.info_if(self.print_debug, f"Flush last message")
            await self.send_to_telegram(f"Cluster name= {nodes_name}")

    @handle_exceptions_async_method
    async def __process_pods__(self, data):
        """
        Data type Pods
        :param data:
        """
        self.print_helper.info_if(self.print_debug, f"Pods received")
        pods_status = data[self.k8s_config.POD_key]
        # await self.__process_pods__(pods_status)

        # 'cs_restart_count'
        # 'cs_ready'
        # 'cs_started'
        # 'cs_state'
        # 'own_controller'
        # 'own_kind'
        # 'own_name'
        await self.__process_key__(data=pods_status,
                                   old_data=self.old_pods,
                                   enable_keys=['cluster',
                                                'namespace',
                                                'started',
                                                'phase',
                                                'own_controller',
                                                'own_kind',
                                                'own_name'],
                                   title='Pod')
        self.old_pods = pods_status

    @handle_exceptions_async_method
    async def __process_stateful_sets__(self, data):
        """
        Data type Stateful sets
        :param data:
        """
        self.print_helper.info_if(self.print_debug, f"Stateful Sets received")
        sts_status = data[self.k8s_config.SS_key]
        # await self.__process_stateful_sets__(sts_status)
        enable_keys = ['cluster',
                       'namespace',
                       'available_replicas',
                       'replicas',
                       ]
        await self.__process_key__(data=sts_status,
                                   old_data=self.old_stateful_set,
                                   enable_keys=enable_keys,
                                   title='Stateful sets')
        self.old_stateful_set = sts_status

    @handle_exceptions_async_method
    async def __process_replica_sets__(self, data):
        """
        Data type replica sets
        :param data:
        """
        self.print_helper.info_if(self.print_debug, f"Replica Sets received")
        sts_status = data[self.k8s_config.RS_key]
        # await self.__process_replica_sets__(sts_status)
        enable_keys = ['cluster',
                       'namespace',
                       'available_replicas',
                       'replicas',
                       ]
        await self.__process_key__(data=sts_status,
                                   old_data=self.old_replica_set,
                                   enable_keys=enable_keys,
                                   title='Replica sets')
        self.old_replica_set = sts_status

    @handle_exceptions_async_method
    async def __process_daemon_sets__(self, data):
        """
        Data type Daemon sets
        :param data:
        """
        self.print_helper.info_if(self.print_debug, f"Daemon Sets received")
        dmn_status = data[self.k8s_config.DS_key]
        # await self.__process_daemon_sets__(dmn_status)
        enable_keys = ['cluster',
                       'namespace',
                       'current_number_scheduled',
                       'desired_number_scheduled',
                       'number_available',
                       'number_ready'

                       ]
        await self.__process_key__(data=dmn_status,
                                   old_data=self.old_daemon_set,
                                   enable_keys=enable_keys,
                                   title='Daemon sets')
        self.old_daemon_set = dmn_status

    @handle_exceptions_async_method
    async def __process_deployment__(self, data):
        """
        Data type Deployment
        :param data:
        """
        self.print_helper.info_if(self.print_debug, f"deployment received")
        dpl_status = data[self.k8s_config.DPL_key]
        enable_keys = ['cluster',
                       'namespace',
                       'available_replicas',
                       'replicas',
                       ]
        await self.__process_key__(data=dpl_status,
                                   old_data=self.old_deployment,
                                   enable_keys=enable_keys,
                                   title='Deployment')
        self.old_deployment = dpl_status

    @handle_exceptions_async_method
    async def __process_pv__(self, data):
        """
        Data type persistent volume
        :param data:
        """
        self.print_helper.info_if(self.print_debug, f"pv received")
        pv_status = data[self.k8s_config.PV_key]
        # await self.__process_pv__(pv_status)
        enable_keys = ['cluster',
                       'namespace',
                       'phase',
                       'storage_class_name',
                       'pv.claim_ref_namespace',
                       ]
        await self.__process_key__(data=pv_status,
                                   old_data=self.old_pv,
                                   enable_keys=enable_keys,
                                   title='PV')
        self.old_pv = pv_status

    @handle_exceptions_async_method
    async def __process_pvc__(self, data):
        """
        Data type persistent volume claims
        :param data:
        """
        self.print_helper.info_if(self.print_debug, f"pvc received")
        pvc_status = data[self.k8s_config.PVC_key]
        enable_keys = ['cluster',
                       'namespace',
                       'phase',
                       'storage_class_name',
                       ]
        await self.__process_key__(data=pvc_status,
                                   old_data=self.old_pvc,
                                   enable_keys=enable_keys,
                                   title='PVC')
        self.old_pvc = pvc_status

    @handle_exceptions_async_method
    async def send_active_configuration(self):
        """
        Send a message to Telegram engine of the active setup
        """
        self.print_helper.info_if(self.print_debug, f"send_active_configuration")
        msg = f'Configuration setup:\n'
        if self.k8s_config is not None:
            msg = msg + f"  - node status= {'ENABLE' if self.k8s_config.NODE_enable else '-'}\n"
            msg = msg + f"  - pods = {'ENABLE' if self.k8s_config.POD_enable else '-'}\n"
            msg = msg + (f"  - deployment= {'ENABLE' if self.k8s_config.DPL_enable else '-'} "
                         f"{'P0' if self.k8s_config.DPL_enable and self.k8s_config.DPL_pods0 else '-'}\n")
            msg = msg + (f"  - stateful sets= {'ENABLE' if self.k8s_config.SS_enable else '-'} "
                         f"{'P0' if self.k8s_config.SS_enable  and self.k8s_config.SS_pods0 else ''}\n")
            msg = msg + (f"  - replicaset= {'ENABLE' if  self.k8s_config.RS_enable else '-'} "
                         f"{'P0' if self.k8s_config.RS_enable and self.k8s_config.RS_pods0 else ''}\n")
            msg = msg + (f"  - daemon sets= {'ENABLE' if self.k8s_config.DS_enable else '-'}"
                         f"{'P0' if  self.k8s_config.DS_enable and  self.k8s_config.DS_pods0 else ''}\n")
            msg = msg + f"  - pvc= {'ENABLE' if self.k8s_config.PVC_enable else '-'}\n"
            msg = msg + f"  - pv= {'ENABLE' if self.k8s_config.PVC_enable else '-'}\n"
        else:
            msg = "Error init config class"

        await self.send_to_telegram(f"k8s-checker is restarted\n{msg}")

    @handle_exceptions_async_method
    async def run(self):
        """
        Main loop of consumer k8s status_run
        """
        try:
            self.print_helper.info("checker run")
            # await self.send_to_telegram("k8s-checker is restarted")
            await self.send_active_configuration()

            while True:
                # get a unit of work
                item = await self.queue.get()

                # check for stop signal
                if item is None:
                    break

                self.print_helper.info_if(self.print_debug,
                                          f"checker new receive element")

                if item is not None:
                    await self.__unpack_data__(item)

            # self.print_helper('checker: end loop')
        except Exception as err:
            # self.print_helper.error(f"consumer error : {err}")
            self.print_helper.error_and_exception(f"run", err)
