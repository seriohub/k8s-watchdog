import asyncio
import os

from utils.print_helper import PrintHelper, LLogger
from utils.config import ConfigProgram, ConfigK8sProcess
from libs.kubernetes_status_run import KubernetesStatusRun
from libs.kubernetes_checker import KubernetesChecker
from libs.kubernetes_telegram import KubernetesTelegram
from utils.handle_error import handle_exceptions_async_method

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
    print(f"INFO    [SYSTEM] start application")
    path_script = os.path.dirname(os.path.realpath(__file__))
    config_prg = ConfigProgram()
    debug_on = config_prg.internal_debug_enable()
    # logger section
    logger_key = config_prg.logger_key()
    logger_format_msg = config_prg.logger_msg_format()
    logger_save_to_file = config_prg.logger_save_to_file()
    logger_folder = config_prg.logger_folder()
    logger_file_name = config_prg.logger_filename()
    logger_file_size = config_prg.logger_max_filesize()
    logger_backup_files = config_prg.logger_his_backups_files()
    logger_level = config_prg.logger_level()
    loop_seconds = config_prg.process_run_sec()
    # telegram section
    telegram_enable = config_prg.telegram_enable()
    telegram_chat_id = config_prg.telegram_chat_id()
    telegram_token = config_prg.telegram_token()
    telegram_max_msg_len = config_prg.telegram_max_msg_len()
    telegram_rate_limit = config_prg.telegram_rate_limit_minute()
    telegram_alive_message = config_prg.telegram_alive_message_hours()

    k8s_load_kube_config_method = config_prg.k8s_load_kube_config_method()
    kube_config_file = config_prg.k8s_config_file()

    # Scrapy configuration
    clk8s = ConfigK8sProcess()
    clk8s.PVC_enable = config_prg.k8s_pvc_enable()
    clk8s.PV_enable = config_prg.k8s_pv_enable()
    clk8s.POD_enable = config_prg.k8s_pods_enable()
    clk8s.NODE_enable = config_prg.k8s_nodes_enable()
    clk8s.DS_enable = config_prg.k8s_daemons_sets_enable()
    clk8s.DPL_enable = config_prg.k8s_deployment_enable()
    clk8s.SS_enable = config_prg.k8s_stateful_sets_enable()
    clk8s.RS_enable = config_prg.k8s_replica_sets_enable()
    clk8s.DS_pods0 = config_prg.k8s_daemons_sets_pods0()
    clk8s.DPL_pods0 = config_prg.k8s_deployment_pods0()
    clk8s.SS_pods0 = config_prg.k8s_stateful_sets_pods0()
    clk8s.RS_pods0 = config_prg.k8s_replica_sets_pods0()

    print(f"INFO    [Process setup] k8s check node={clk8s.NODE_enable}")
    print(f"INFO    [Process setup] k8s check daemon sets={clk8s.DS_enable}- pods0={clk8s.DS_pods0}")
    print(f"INFO    [Process setup] k8s check pods ={clk8s.POD_enable}")
    print(f"INFO    [Process setup] k8s check deployment={clk8s.DPL_enable}- pods0={clk8s.DPL_pods0}")
    print(f"INFO    [Process setup] k8s check stateful sets={clk8s.SS_enable}- pods0={clk8s.SS_pods0}")
    print(f"INFO    [Process setup] k8s check replicaset={clk8s.RS_enable}- pods0={clk8s.RS_pods0}")
    print(f"INFO    [Process setup] k8s check pvc={clk8s.PVC_enable}")
    print(f"INFO    [Process setup] k8s check pv={clk8s.PVC_enable}")

    logger = init_logger.init_logger(key=logger_key,
                                     output_format=logger_format_msg,
                                     save_to_file=logger_save_to_file,
                                     destination_folder=logger_folder,
                                     filename=logger_file_name,
                                     max_file_size=logger_file_size,
                                     historical_files=logger_backup_files,
                                     level=logger_level)
    print_helper.set_logger(logger)
    if logger is None:
        print("[INFO]   Logger does not start")
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
                           clk8s
                           ))
