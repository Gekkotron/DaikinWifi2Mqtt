import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import config
import json
from Logger import Logger
from Events import Events

ENALE_LOGGING = True


class Mqtt:
    def __init__(self):
        self.client = None

        broker = Events().broker

        @broker.on(config.MQTT_GATEWAY_PUBLISH_TOPIC)
        def controlResult(payload):
            self.publish(payload["topic"], payload["response"])

    # Begin the program
    def on_connect(self, client, userdata, flags, reasonCode):
        if(ENALE_LOGGING):
            Logger().info(f"Mqtt : Connected mqtt sub to daikin/# {str(reasonCode)}")
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(config.MQTT_GATEWAY_BASE_TOPIC + "#")

    def on_message(self, client, userdata, msg):
        if(ENALE_LOGGING):
            Logger().info(f"Mqtt : on_message: {msg.topic} -> {msg.payload}")
        payload_decoded = msg.payload.decode('utf-8').replace("\"", "")
        payload = json.loads(msg.payload)
        payload["topic"] = msg.topic
        Events().broker.emit(config.MQTT_GATEWAY_MESSAGE, payload)

    def on_log(self, client, userdata, level, buf):
        if(ENALE_LOGGING):
            Logger().info(f"Mqtt : on_log: {buf}")

    def connect(self):
        self.client = mqtt.Client("Daikin gateway")
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        # self.client.on_log = self.on_log
        if(ENALE_LOGGING):
            Logger().info("Mqtt : Connecting to mqtt broker")
        try:
            self.client.connect(config.MQTT_HOST, config.MQTT_PORT, 60)
        except ConnectionRefusedError:
            if(ENALE_LOGGING):
                Logger().info("Mqtt : ConnectionRefusedError")

    def loop_stop(self):
        self.client.loop_stop()

    def loop_start(self):
        self.client.loop_start()

    def update_status(self, status):
        self.publish(config.MQTT_GATEWAY_STATUS_CMD, {"status": status})

    def publish_event(self, topic, payload):
        publish.single(topic=topic, payload=json.dumps(payload))

    def publish(self, cmd, data):
        try:
            self.publish_event(cmd, data)
        except OSError:
            Logger().info("Mqtt : OSError")
        except ConnectionRefusedError:
            Logger().info("Mqtt : ConnectionRefusedError")
