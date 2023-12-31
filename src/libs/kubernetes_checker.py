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
                 dispatcher_queue=None,
                 dispatcher_max_msg_len=8000,
                 dispatcher_alive_message_hours=24,
                 k8s_key_config: ConfigK8sProcess = None):

        self.print_helper = PrintHelper('k8s_checker', logger)
        self.print_debug = debug_on

        self.print_helper.debug_if(self.print_debug,
                                   f"__init__")

        self.queue = queue

        self.dispatcher_max_msg_len = dispatcher_max_msg_len
        self.dispatcher_queue = dispatcher_queue

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

        self.alive_message_seconds = dispatcher_alive_message_hours * 3600
        self.last_send = calendar.timegm(datetime.today().timetuple())

        self.cluster_name = ""
        self.force_alive_message = True

        # LS 2023.11.02 add variable for sending isolate message configuration
        self.send_config = False

        # LS 2023.11.03 add final message for concat data all keys in a one message
        # Not required a unique message
        self.final_message = ""
        # Not required a unique message
        self.unique_message = False

    @handle_exceptions_async_method
    async def __put_in_queue__(self,
                               queue,
                               obj):
        """
        Add new element to the queue
        :param queue: reference to a queue
        :param obj: objet to add
        """
        self.print_helper.info_if(self.print_debug, "__put_in_queue__")

        await queue.put(obj)

    @handle_exceptions_async_method
    async def send_to_dispatcher(self, message, force_message=False):
        """
        Send message to dispatcher engine
        @param force_message: send message immediately
        @param message: message to send
        """
        self.print_helper.info(f"send_to_dispatcher. msg len= {len(message)}")
        if len(message) > 0:
            if not self.unique_message or force_message:
                self.last_send = calendar.timegm(datetime.today().timetuple())
                await self.__put_in_queue__(self.dispatcher_queue,
                                            message)
            else:

                if len(self.final_message) > 0:
                    self.print_helper.info(f"send_to_dispatcher. concat message- len({len(self.final_message)})")
                    self.final_message = f"{self.final_message}\n{'-'*20}\n{message}"
                else:
                    self.print_helper.info(f"send_to_dispatcher. start message")
                    self.final_message = f"{message}"

    @handle_exceptions_async_method
    async def send_to_dispatcher_summary(self):
        """
        Send summary message to dispatcher engine
        """

        self.print_helper.info(f"send_to_dispatcher_summary. message-len= {len(self.final_message)}")
        # Chck if the final message is not empty
        if len(self.final_message) > 10:
            self.final_message = f"Start report\n{self.final_message}\nEnd report"
            self.last_send = calendar.timegm(datetime.today().timetuple())
            await self.__put_in_queue__(self.dispatcher_queue,
                                        self.final_message)

        self.final_message = ""
        self.unique_message = False

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
                            # LS 2023.10.29 update
                            # if old_data[key_dict] == current_node:
                            self.print_helper.info_if(self.print_debug, f"{title} old data for {key_dict}  "
                                                                        f"is equal to new data. No message")
                            process = False

                    if process:
                        # msg = f'{title} detail\n'
                        msg += f"----------\n"
                        # msg += f"Name= {key_dict}\n"
                        msg += f"{key_dict}\n"
                        # print(f"current_node:{current_node}")
                        for key, value in current_node.items():
                            key_value = True
                            if (enable_keys is None or
                                    key in enable_keys):
                                key_value, msg = await self.__concatenate__status__(key, key_value, msg, value)
                            else:
                                key_value = False

                            if key_value:
                                if (value is not None
                                        and len(str(value)) > 0):
                                    msg += f"{key}= {value}\n"

                        # if resolved:
                        #     msg += f"Resolved= True\n"

                        if len(msg) >= self.dispatcher_max_msg_len:
                            self.print_helper.info_if(self.print_debug,
                                                      f"Max message length reached, force send message")
                            await self.send_to_dispatcher(msg)
                            # Reset msg len
                            msg = base_title

                    else:
                        self.print_helper.info_if(self.print_debug,
                                                  f"{title} set {key_dict} already status sent")

                if len(msg) > len(base_title):
                    self.print_helper.info_if(self.print_debug, f"Flush last message")

                    await self.send_to_dispatcher(msg)

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

    async def __concatenate__status__(self, key, key_value, msg, value):
        """
        concatenate the message. Iterate in the f
        @param key: title of section
        @param key_value:
        @param msg: concatenate variable
        @param value: dict value
        @return:
        """
        if isinstance(value, dict):
            key_value = False
            msg += f"{key}:\n"
            for key_n, value_n in value.items():
                if value_n is not None and len(value_n) > 0:
                    if not isinstance(value_n, dict):
                        msg += f"   {key_n}= {value_n}\n"
                    else:
                        key_value, msg = await self.__concatenate__status__(key_n,
                                                                            key_value,
                                                                            msg,
                                                                            value_n)

        return key_value, msg

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
                # LS 2023.11.03 add key message for sending unique message
                elif self.k8s_config.disp_MSG_key_start in data:
                    self.unique_message = True
                    self.final_message = ""
                # LS 2023.11.03 add key message for sending unique message
                elif self.k8s_config.disp_MSG_key_end in data:
                    await self.send_to_dispatcher_summary()
                else:
                    self.print_helper.info(f"key not defined")
            else:
                self.print_helper.info(f"__unpack_data.the message is not a type of dict")

            # dispatcher alive message
            if self.alive_message_seconds > 0:
                diff = calendar.timegm(datetime.today().timetuple()) - self.last_send
                # add parameter force message
                if diff > self.alive_message_seconds or self.force_alive_message:
                    self.print_helper.info(f"__unpack_data.send alive message")
                    await self.send_to_dispatcher(f"Cluster: {self.cluster_name}"
                                                  f"\nk8s-watchdog is running."
                                                  f"\nThis is an alive message"
                                                  f"\nNo warning/errors were triggered in the last "
                                                  f"{int(self.alive_message_seconds / 3600)} "
                                                  f"hours ", True)
                    self.force_alive_message = False

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
        """
        Obtain cluster name
        @param data:
        """
        self.print_helper.info(f"__process_cluster_name__")

        nodes_name = data[self.k8s_config.CLUSTER_Name_key]

        self.print_helper.info(f"cluster name {nodes_name}")
        if nodes_name is not None:
            self.print_helper.info_if(self.print_debug, f"Flush last message")
            # LS 2023.11.04 Send configuration separately
            if self.send_config:
                await self.send_to_dispatcher(f"Cluster name= {nodes_name}")
            else:
                await self.send_active_configuration(f"Cluster name= {nodes_name}")

        self.cluster_name = nodes_name

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

        # LS 2023.10.28 add key condition_x
        # LS 2023.10.28 remove 'phase',
        await self.__process_key__(data=pods_status,
                                   old_data=self.old_pods,
                                   enable_keys=['cluster',
                                                'namespace',
                                                'started',
                                                'own_controller',
                                                'own_kind',
                                                'own_name',
                                                'conditions',
                                                'cs_0',
                                                'cs_1',
                                                'cs_2',
                                                'cs_3'],
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
    async def send_active_configuration(self, sub_title=None):
        """
        Send a message to Telegram engine of the active setup
        """
        title = "k8s-watchdog is restarted"
        if sub_title is not None and len(sub_title) > 0:
            title = f"{title}\n{sub_title}"

        self.print_helper.info_if(self.print_debug, f"send_active_configuration")

        msg = f'Configuration setup:\n'
        if self.k8s_config is not None:
            msg = msg + f"  . node status= {'ENABLE' if self.k8s_config.NODE_enable else '.'}\n"
            msg = msg + f"  . pods = {'ENABLE' if self.k8s_config.POD_enable else '.'}\n"
            msg = msg + (f"  . deployment= {'ENABLE' if self.k8s_config.DPL_enable else '.'} "
                         f"{'P0' if self.k8s_config.DPL_enable and self.k8s_config.DPL_pods0 else ''}\n")
            msg = msg + (f"  . stateful sets= {'ENABLE' if self.k8s_config.SS_enable else '.'} "
                         f"{'P0' if self.k8s_config.SS_enable and self.k8s_config.SS_pods0 else ''}\n")
            msg = msg + (f"  . replicaset= {'ENABLE' if self.k8s_config.RS_enable else '.'} "
                         f"{'P0' if self.k8s_config.RS_enable and self.k8s_config.RS_pods0 else ''}\n")
            msg = msg + (f"  . daemon sets= {'ENABLE' if self.k8s_config.DS_enable else '-'}"
                         f"{'P0' if self.k8s_config.DS_enable and self.k8s_config.DS_pods0 else ''}\n")
            msg = msg + f"  . pvc= {'ENABLE' if self.k8s_config.PVC_enable else '.'}\n"
            msg = msg + f"  . pv= {'ENABLE' if self.k8s_config.PVC_enable else '.'}\n"
            if self.alive_message_seconds >= 3600:
                msg = msg + f"\nAlive message every {int(self.alive_message_seconds / 3600)} hours"
            else:
                msg = msg + f"\nAlive message every {int(self.alive_message_seconds / 60)} minutes"
        else:
            msg = "Error init config class"

        msg = f"{title}\n\n{msg}"
        await self.send_to_dispatcher(msg)

    @handle_exceptions_async_method
    async def run(self):
        """
        Main loop of consumer k8s status_run
        """
        try:
            self.print_helper.info("checker run")
            if self.send_config:
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
