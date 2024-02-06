import sys
import threading
from typing import Callable
from wsgiref.simple_server import make_server

from loguru import logger
from prometheus_client import make_wsgi_app

from vk_bot.config import LOG_LEVEL
from vk_bot.handlers import run_bot_polling


def _configure_logger():
    logger.remove()
    logger.add(
        "/var/log/scbot/vk_bot.log", rotation="100 MB", level=LOG_LEVEL, diagnose=True
    )
    logger.add(sys.stderr, level=LOG_LEVEL, diagnose=True)


def _start_metrics_handler(host, port) -> Callable[[], None]:
    app = make_wsgi_app()
    httpd = make_server(host, port, app)
    metrics_thread = threading.Thread(target=httpd.serve_forever)
    metrics_thread.start()

    logger.info("The metrics handler is running")

    def shutdown():
        httpd.shutdown()
        metrics_thread.join()

    return shutdown


def start():
    _configure_logger()
    shutdown_metrics_handler = _start_metrics_handler("", 8000)

    try:
        logger.info("Launching an event handler from VK")
        run_bot_polling()
    except Exception as error:
        logger.error(error)

    shutdown_metrics_handler()


if __name__ == "__main__":
    start()
