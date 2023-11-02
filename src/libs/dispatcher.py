import asyncio
import requests
from datetime import datetime
from utils.config import ConfigK8sProcess
from utils.config import ConfigDispatcher
from utils.print_helper import PrintHelper
from utils.handle_error import handle_exceptions_async_method


class Dispatcher:
    """
    Provide a wrapper for sending data over different channels
    """

    def __init__(self,
                 debug_on=True,
                 logger=None,
                 queue=None,
                 queue_telegram=None,
                 queue_mail=None,
                 dispatcher_config: ConfigDispatcher = None,
                 k8s_key_config: ConfigK8sProcess = None):

        self.print_helper = PrintHelper('dispatcher', logger)
        self.print_debug = debug_on

        self.print_helper.debug_if(self.print_debug,
                                   f"__init__")

        self.k8s_config = ConfigK8sProcess()
        if k8s_key_config is not None:
            self.k8s_config = k8s_key_config

        self.dispatcher_config = ConfigDispatcher()
        if dispatcher_config is not None:
            self.dispatcher_config = dispatcher_config

        # LS 2023.11.02 add to comment, not used
        # self.execute_routine = True
        self.queue = queue
        # LS 2023.11.02 add specif queue for the telegram channel
        self.queue_telegram = queue_telegram
        # LS 2023.11.02 add specif queue for the email channel
        self.queue_mail = queue_mail

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
    async def run(self):
        try:
            self.print_helper.info(f"dispatcher run active")
            while True:
                # get a unit of work
                item = await self.queue.get()

                # check for stop signal
                if item is None:
                    break

                self.print_helper.info_if(self.print_debug,
                                          f"dispatcher new receive element")

                if item is not None:
                    if self.dispatcher_config.telegram_enable:
                        await self.__put_in_queue__(self.queue_telegram,
                                                    item)

                    if self.dispatcher_config.email_enable:
                        await self.__put_in_queue__(self.queue_mail,
                                                    item)

                # self.print_helper('dispatcher: end loop')
        except Exception as err:
            self.print_helper.error_and_exception(f"run", err)
