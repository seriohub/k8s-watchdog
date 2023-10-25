import asyncio
import os

from utils.print_helper import PrintHelper, LLogger
from utils.config import ConfigProgram, ConfigK8sProcess
from libs.kubernetes_status_run import KubernetesStatusRun
from libs.kubernetes_checker import KubernetesChecker
from libs.kubernetes_telegram import KubernetesTelegram
from utils.handle_error import handle_exceptions_async_method
from utils.version import __version__
from utils.version import __date__


# init logger engine
init_logger = LLogger()
logger = None
debug_on = True
print_helper = PrintHelper('K8s', None)


# entry point coroutine
@handle_exceptions_async_method
async def main_start(seconds=120,
                     load_kube_config=False,
                     config_file=None,
                     telegram_enabled=False,
                     telegram_token_id='',
                     telegram_id='',
                     telegram_max_len=2000,
                     telegram_rate_minute=10,
                     telegram_alive_msg_hours=0,
                     k8s_class: ConfigK8sProcess = None):
    """

    :param telegram_alive_msg_hours: 
    :param seconds:
    :param load_kube_config:
    :param config_file:
    :param telegram_enabled:
    :param telegram_token_id:
    :param telegram_id:
    :param telegram_max_len:
    :param telegram_rate_minute:
    :param k8s_class:
    """
    # create the shared queue
    queue = asyncio.Queue()
    queue_telegram = asyncio.Queue()

    # Force separate telegram handler
    telegram_separate_cor = True

    k8s_stat_read = KubernetesStatusRun(kube_load_method=load_kube_config,
                                        kube_config_file=config_file,
                                        debug_on=debug_on,
                                        logger=logger,
                                        queue=queue,
                                        cycles_seconds=seconds,
                                        k8s_key_config=k8s_class)

    k8s_stat_checker = KubernetesChecker(debug_on=debug_on,
                                         logger=logger,
                                         queue=queue,
                                         telegram_queue=queue_telegram,
                                         telegram_max_msg_len=telegram_max_len,
                                         telegram_alive_message_hours=telegram_alive_msg_hours,
                                         k8s_key_config=k8s_class
                                         )
    k8s_stat_telegram = KubernetesTelegram(debug_on=debug_on,
                                           logger=logger,
                                           queue=queue_telegram,
                                           telegram_enable=telegram_enabled,
                                           telegram_separate=telegram_separate_cor,
                                           telegram_api_token=telegram_token_id,
                                           telegram_chat_id=telegram_id,
                                           telegram_max_msg_len=telegram_max_len,
                                           telegram_rate_minute=telegram_rate_minute,
                                           k8s_key_config=k8s_class
                                           )

    # loop = asyncio.get_event_loop()
    try:
        while True:
            print_helper.info("try to restart the service")
            # run the producer and consumers
            if telegram_separate_cor:
                await asyncio.gather(k8s_stat_read.run(),
                                     k8s_stat_checker.run(),
                                     k8s_stat_telegram.run())
            else:
                await asyncio.gather(k8s_stat_read.run(),
                                     k8s_stat_checker.run())
            print_helper.info("the service is not in run")

    except KeyboardInterrupt:
        print_helper.wrn("user request stop")
        pass
    except Exception as e:
        # print_helper.error(traceback.format_exception(*sys.exc_info()))
        print_helper.error_and_exception(f"main_start", e)


if __name__ == "__main__":
    print(f"INFO    [SYSTEM] start application version {__version__} release date {__date__}")
    path_script = os.path.dirname(os.path.realpath(__file__))
    config_prg = ConfigProgram(debug_on=debug_on)
    debug_on = config_prg.internal_debug_enable()
    clk8s_setup = ConfigK8sProcess(config_prg)

    # telegram section
    telegram_enable = config_prg.telegram_enable()
    telegram_chat_id = config_prg.telegram_chat_id()
    telegram_token = config_prg.telegram_token()
    telegram_max_msg_len = config_prg.telegram_max_msg_len()
    telegram_rate_limit = config_prg.telegram_rate_limit_minute()
    telegram_alive_message = config_prg.telegram_alive_message_hours()

    # kube config method
    k8s_load_kube_config_method = config_prg.k8s_load_kube_config_method()
    kube_config_file = config_prg.k8s_config_file()
    loop_seconds = config_prg.process_run_sec()

    logger = init_logger.init_logger_from_config(cl_config=config_prg)

    print_helper.set_logger(logger)
    if logger is None:
        print("[ERROR]   Logger does not start")
    else:
        print_helper.info("start Check service")

    print_helper.info("start Watchdog")
    asyncio.run(main_start(loop_seconds,
                           k8s_load_kube_config_method,
                           kube_config_file,
                           telegram_enable,
                           telegram_token,
                           telegram_chat_id,
                           telegram_max_msg_len,
                           telegram_rate_limit,
                           telegram_alive_message,
                           clk8s_setup
                           ))
