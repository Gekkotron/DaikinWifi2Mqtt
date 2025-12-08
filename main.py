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
    Logger().info("Main : Daikin MQTT Gateway started.")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        Logger().info('Main : Interrupted by user')
    except Exception as e:
        Logger().info(f"Main : Exception occurred: {str(e)}\n{traceback.format_exc()}")
        mqtt.publish_event(config.MQTT_GATEWAY_ERROR_CMD, traceback.format_exc())
    finally:
        Logger().info("Main : Shutting down Daikin MQTT Gateway.")
        mqtt.loop_stop()


if __name__ == "__main__":
    app()
