import config
from Logger import Logger
from Mqtt import Mqtt
from daikinapi import Daikin
import time
import sys
import traceback

mqtt = Mqtt()
daikin = Daikin()

def app():
    mqtt.connect()
    mqtt.loop_start()

    #mqtt.update_status(config.MQTT_GATEWAY_STATUS_START)
    #mqtt.publish(config.MQTT_GATEWAY_ERROR_CMD, "")

    while True:
        time.sleep(0.1)

    #mqtt.update_status(config.MQTT_GATEWAY_STATUS_QUIT)
    mqtt.loop_stop()


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        Logger().info('Main : Interrupted')
        exit()
    except Exception as e:
        Logger().info(f"Main : Oops! {str(sys.exc_info())} occured. \n {traceback.format_exc()}\n")
        mqtt.publish_event(config.MQTT_GATEWAY_ERROR_CMD, traceback.format_exc())
