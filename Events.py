import config
from pyee import EventEmitter
import threading


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
class Events():
    def __init__(self):
        self.broker = EventEmitter()
