import logging
from logging.handlers import TimedRotatingFileHandler
import os
import config
import http.server
from socketserver import TCPServer
import threading
import time


def singleton(cls):
    instances = {}
    lock = threading.Lock()

    def ctor(*args, **kwargs):
        if cls not in instances:
            with lock:
                # Double-check pattern to avoid race condition
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return ctor


@singleton
class Logger():
    def __init__(self):
        import sys
        import traceback
        print(f"\n[DEBUG] ===== Logger.__init__() called =====", file=sys.stderr, flush=True)
        print(f"[DEBUG] Call stack:", file=sys.stderr, flush=True)
        for line in traceback.format_stack()[:-1]:
            print(line.strip(), file=sys.stderr, flush=True)

        directory = "logs"
        filename = "Daikin"
        if not os.path.exists(directory):
            os.makedirs(directory)

        path = directory + "/" + filename
        should_roll_over = os.path.isfile(path)

        # create formatter
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # create logger
        self.logger = logging.getLogger("logging")
        print(f"[DEBUG] Logger ID: {id(self.logger)}, Current handlers: {len(self.logger.handlers)}", file=sys.stderr, flush=True)
        self.logger.setLevel(logging.DEBUG)

        # Disable auto log in console
        self.logger.propagate = False

        # Clear any existing handlers to prevent duplicates
        self.logger.handlers.clear()
        print(f"[DEBUG] After clear: {len(self.logger.handlers)} handlers", file=sys.stderr, flush=True)

        fileHandler = TimedRotatingFileHandler(path, when="d", interval=4)
        fileHandler.suffix = "_%Y-%m-%d_%H-%M-%S.log"
        if should_roll_over:  # log already exists, roll over!
            fileHandler.doRollover()

        streamHandler = logging.StreamHandler()
        streamHandler.setLevel(logging.DEBUG)

        fileHandler.setFormatter(formatter)
        streamHandler.setFormatter(formatter)

        self.logger.addHandler(fileHandler)
        self.logger.addHandler(streamHandler)
        print(f"[DEBUG] After adding: {len(self.logger.handlers)} handlers", file=sys.stderr, flush=True)
        print(f"[DEBUG] ===== End Logger.__init__() =====\n", file=sys.stderr, flush=True)


    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        import sys
        print(f"[DEBUG] info() - Logger ID: {id(self.logger)}, handlers: {len(self.logger.handlers)}, msg: {msg[:50]}", file=sys.stderr, flush=True)
        self.logger.info(msg)

    def warn(self, msg):
        self.logger.warn(msg)

    def error(self, msg):
        self.logger.error(msg)

    def critical(self, msg):
        self.logger.critical(msg)

