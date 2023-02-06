import logging
from logging.handlers import TimedRotatingFileHandler
import os
import http.server
from socketserver import TCPServer
import threading


def singleton(cls):
    instance = None

    def ctor(*args, **kwargs):
        nonlocal instance
        if not instance:
            instance = cls(*args, **kwargs)
        return instance
    return ctor


@singleton
class Logger():
    def __init__(self):
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
        self.logger.setLevel(logging.DEBUG)

        # Disable auto log in console
        self.logger.propagate = False

        # create rotating file handler
        fileHandler = TimedRotatingFileHandler(path, when="d", interval=4)
        fileHandler.suffix = "_%Y-%m-%d_%H-%M-%S.log"
        if should_roll_over:  # log already exists, roll over!
            fileHandler.doRollover()

        # create console handler and set level to debug
        streamHandler = logging.StreamHandler()
        streamHandler.setLevel(logging.DEBUG)

        # add formatter to handler
        fileHandler.setFormatter(formatter)
        streamHandler.setFormatter(formatter)

        # add handlers to logger
        self.logger.addHandler(fileHandler)
        self.logger.addHandler(streamHandler)

        # Launch the http server allow to access the logs folder over local network
        server_thread = threading.Thread(target=self.simpleHttpServer)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg):
        self.logger.error(msg)

    def critical(self, msg):
        self.logger.critical(msg)

    def handler_from(self, directory):
        def _init(self, *args, **kwargs):
            return http.server.SimpleHTTPRequestHandler.__init__(self, *args, directory=self.directory, **kwargs)
        return type(f'HandlerFrom<{directory}>', (http.server.SimpleHTTPRequestHandler,),
                    {'__init__': _init,
                    'directory': directory})

    def simpleHttpServer(self):
        PORT = 8000

        try:
            httpd = TCPServer(("", PORT), self.handler_from("logs"), bind_and_activate=False)

            if(httpd is not None):
                self.info(f"Logger - Launch http server for logs at 192.168.1.100:{str(PORT)}")
                httpd.allow_reuse_address = True
                httpd.server_bind()
                httpd.server_activate()
                httpd.serve_forever()
        except OSError:
            self.logger.error("Logger - simpleHttpServer error")
