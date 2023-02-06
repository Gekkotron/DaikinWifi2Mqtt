import config
from Logger import Logger
from Mqtt import Mqtt
from daikinapi import Daikin
from Events import Events
import time
import sys
import traceback

mqtt = Mqtt()
daikin = Daikin()

def app():
    mqtt.connect()
    mqtt.loop_start()

    while True:
        time.sleep(0.1)

    mqtt.loop_stop()


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        Logger().info('Main : Interrupted')
        sys.exit()
    except Exception:
        Logger().info(f"Main : Oops! {str(sys.exc_info())} occured. \n {traceback.format_exc()}\n")
        Events().broker.emit(config.MQTT_GATEWAY_ERROR_CMD, {"topic": "daikin/error", "error": traceback.format_exc()})
