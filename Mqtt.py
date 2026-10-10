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
        if reasonCode != 0:
            Logger().error(f"Mqtt : Connection refused ({mqtt.connack_string(reasonCode)}), check MQTT_USERNAME / MQTT_PASSWORD")
            return
        client.subscribe(config.MQTT_GATEWAY_BASE_TOPIC + "#")
        client.publish(config.MQTT_GATEWAY_AVAILABILITY_TOPIC, "online", retain=True)
        if config.HA_DISCOVERY_ENABLED:
            # Home Assistant birth message: announce again when HA restarts
            client.subscribe(config.HA_DISCOVERY_PREFIX + "/status")
            Events().broker.emit(config.HA_CONNECTED)

    def on_message(self, client, userdata, msg):
        if(ENALE_LOGGING):
            Logger().info(f"Mqtt : on_message: {msg.topic} -> {msg.payload}")
        if self._route_home_assistant(msg):
            return
        try:
            payload_decoded = msg.payload.decode('utf-8')
            if not payload_decoded.strip():
                Logger().warning(f"Mqtt : Received empty payload for topic {msg.topic}, skipping parsing.")
                return
            payload = json.loads(payload_decoded)
            topic_parts = msg.topic.split('/')
            cmd = topic_parts[2] if len(topic_parts) > 2 else ""
            # Allow payloads without 'key' and 'value' for 'refresh', 'sensor', and 'data' and 'status' commands
            if cmd in ["refresh", "sensor", "data", "status"]:
                payload["topic"] = msg.topic
                Events().broker.emit(config.MQTT_GATEWAY_MESSAGE, payload)
                return
            if not isinstance(payload, dict) or "key" not in payload or "value" not in payload:
                Logger().error(f"Mqtt : Invalid payload format: {payload_decoded}")
                return
            payload["topic"] = msg.topic
            Events().broker.emit(config.MQTT_GATEWAY_MESSAGE, payload)
        except Exception as e:
            Logger().error(f"Mqtt : Error parsing payload: {e}, raw: {msg.payload}")

    def _route_home_assistant(self, msg):
        """ Handles HA topics and the bridge's own non-JSON topics. Returns True when the message is consumed. """
        topic_parts = msg.topic.split('/')
        if msg.topic == config.HA_DISCOVERY_PREFIX + "/status":
            if config.HA_DISCOVERY_ENABLED and msg.payload.decode('utf-8', 'replace').strip() == "online":
                Events().broker.emit(config.HA_CONNECTED)
            return True
        if msg.topic == config.MQTT_GATEWAY_AVAILABILITY_TOPIC:
            return True
        # daikin/<host>/ha/state (our own state) or daikin/<host>/ha/<field>/set (command)
        if len(topic_parts) >= 3 and topic_parts[2] == "ha":
            if config.HA_DISCOVERY_ENABLED and len(topic_parts) == 5 and topic_parts[4] == "set":
                Events().broker.emit(config.HA_COMMAND, {
                    "host": topic_parts[1],
                    "field": topic_parts[3],
                    "value": msg.payload.decode('utf-8', 'replace'),
                })
            return True
        return False

    def on_log(self, client, userdata, level, buf):
        if(ENALE_LOGGING):
            Logger().info(f"Mqtt : on_log: {buf}")

    def connect(self):
        import time
        import threading
        if hasattr(self, "_mqtt_thread_started") and self._mqtt_thread_started:
            Logger().info("Mqtt : connect() called but MQTT thread already running.")
            return
        def on_disconnect(client, userdata, rc):
            Logger().error(f"Mqtt : Disconnected from broker (rc={rc}). Attempting to reconnect...")
        self.client = mqtt.Client("Daikin gateway")
        if config.MQTT_USERNAME:
            self.client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
        self.client.will_set(config.MQTT_GATEWAY_AVAILABILITY_TOPIC, "offline", retain=True)
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = on_disconnect
        # self.client.on_log = self.on_log
        def mqtt_thread():
            while True:
                try:
                    if(ENALE_LOGGING):
                        Logger().info("Mqtt : Connecting to mqtt broker")
                    self.client.connect(config.MQTT_HOST, config.MQTT_PORT, 60)
                    self.client.loop_forever()
                except Exception as e:
                    Logger().error(f"Mqtt : MQTT thread error: {e}, retrying in 5s")
                    time.sleep(5)
        t = threading.Thread(target=mqtt_thread, daemon=True)
        t.start()
        self._mqtt_thread_started = True

    def loop_stop(self):
        self.client.loop_stop()

    def loop_start(self):
        # No-op: handled by dedicated thread in connect()
        pass

    def update_status(self, status):
        self.publish(config.MQTT_GATEWAY_STATUS_CMD, {"status": status})

    def publish_event(self, topic, payload, retain=False):
        if self.client:
            try:
                self.client.publish(topic, json.dumps(payload), retain=retain)
            except Exception as e:
                Logger().error(f"Mqtt : Publish error: {e}")
        else:
            Logger().error("Mqtt : Client not connected, cannot publish.")

    def publish(self, cmd, data):
        try:
            self.publish_event(cmd, data)
        except OSError:
            Logger().info(f"Mqtt : OSError {cmd} {data}")
        except ConnectionRefusedError:
            Logger().info("Mqtt : ConnectionRefusedError")
