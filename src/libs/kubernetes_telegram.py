import asyncio
import requests
from datetime import datetime
from utils.config import ConfigK8sProcess
from utils.print_helper import PrintHelper
from utils.handle_error import handle_exceptions_async_method


class KubernetesTelegram:
    """
    Provide a wrapper for sending data over Telegram
    """

    def __init__(self,
                 debug_on=True,
                 logger=None,
                 queue=None,
                 telegram_enable=True,
                 telegram_separate=True,
                 telegram_api_token='',
                 telegram_chat_id='',
                 telegram_max_msg_len=2000,
                 telegram_rate_minute=10,
                 k8s_key_config: ConfigK8sProcess = None):

        self.print_helper = PrintHelper('k8s_telegram', logger)
        self.print_debug = debug_on

        self.print_helper.debug_if(self.print_debug,
                                   f"__init__")

        self.k8s_config = ConfigK8sProcess()
        if k8s_key_config is not None:
            self.k8s_config = k8s_key_config

        self.execute_routine = telegram_separate
        self.queue = queue
        self.telegram_api_token = telegram_api_token
        self.telegram_chat_ID = telegram_chat_id
        self.telegram_enable = telegram_enable
        self.telegram_max_msg_len = telegram_max_msg_len
        self.telegram_rate_minute = telegram_rate_minute

        self.telegram_last_minute = 0
        self.telegram_last_rate = 0

    @handle_exceptions_async_method
    async def __can_send_message__(self):
        try:
            self.print_helper.info(f"__can_send_message__"
                                   f"{self.telegram_last_rate}/{self.telegram_rate_minute}")
            self.telegram_last_rate += 1
            seconds_waiting = 0
            while True:
                my_data = datetime.now()
                if my_data.minute != self.telegram_last_minute:
                    self.telegram_last_minute = my_data.minute
                    self.telegram_last_rate = 0

                if self.telegram_last_rate <= self.telegram_rate_minute:
                    break
                if seconds_waiting % 30 == 0:
                    self.print_helper.info(f"...wait {60 - my_data.second} seconds. "
                                           f"Max rate minute reached {self.telegram_rate_minute}")

                await asyncio.sleep(1)
                seconds_waiting += 1

        except Exception as err:
            self.print_helper.error_and_exception(f"__can_send_message__", err)

    @handle_exceptions_async_method
    async def send_to_telegram(self, message):
        self.print_helper.info(f"send_to_telegram")
        await self.__can_send_message__()
        if self.telegram_enable:
            if len(self.telegram_api_token) > 0 and len(self.telegram_chat_ID) > 0:
                api_url = f'https://api.telegram.org/bot{self.telegram_api_token}/sendMessage'
                try:

                    response = requests.post(api_url, json={'chat_id': self.telegram_chat_ID,
                                                            'text': message})
                    # LS 2023.10.28 truncate the response
                    self.print_helper.info(f"send_to_telegram.response {response.text[1:10]}")

                except Exception as e:
                    # self.print_helper.error(f"send_to_telegram. error {e}")
                    self.print_helper.error_and_exception(f"send_to_telegram", e)
            else:
                if len(self.telegram_api_token) == 0:
                    self.print_helper.error(f"send_to_telegram. api token is not defined")
                if len(self.telegram_chat_ID) == 0:
                    self.print_helper.error(f"send_to_telegram. chatID is not defined")
        else:
            self.print_helper.info(f"send_to_telegram[Disable send...only std out]={message}")

    @handle_exceptions_async_method
    async def run(self):
        try:
            self.print_helper.info(f"telegram run Active: {self.execute_routine}")
            # last_send = 0
            if self.execute_routine:
                while True:
                    # get a unit of work
                    item = await self.queue.get()

                    # check for stop signal
                    if item is None:
                        break

                    self.print_helper.info_if(self.print_debug,
                                              f"telegram new receive element")

                    if item is not None:
                        await self.send_to_telegram(item)

                # self.print_helper('telegram: end loop')
        except Exception as err:
            self.print_helper.error_and_exception(f"run", err)
