import config
import ha_discovery
from Logger import Logger
from Events import Events
import threading
import time


class HomeAssistant:
    """ Announces DAIKIN_HOSTS units through Home Assistant MQTT discovery, polls them and applies HA commands """

    def __init__(self, mqtt, daikin):
        self.mqtt = mqtt
        self.daikin = daikin
        # Daikin adapters handle one request at a time: serialize polls and commands
        self.lock = threading.Lock()

        broker = Events().broker

        @broker.on(config.HA_CONNECTED)
        def connected():
            self.publish_discovery()
            threading.Thread(target=self.poll_all, daemon=True).start()

        @broker.on(config.HA_COMMAND)
        def command(payload):
            # Off the MQTT network thread: the HTTP round trips can take seconds
            threading.Thread(target=self.handle_command, args=(payload["host"], payload["field"], payload["value"]), daemon=True).start()

    def start(self):
        if not config.DAIKIN_HOSTS:
            Logger().warning("HomeAssistant : HA_DISCOVERY_ENABLED but DAIKIN_HOSTS is empty, nothing to announce")
            return
        if config.DAIKIN_POLL_INTERVAL > 0:
            threading.Thread(target=self._poll_loop, daemon=True).start()

    def publish_discovery(self):
        for host, name in config.DAIKIN_HOSTS.items():
            for topic, payload in ha_discovery.discovery_messages(config.HA_DISCOVERY_PREFIX, host, name, config.MQTT_GATEWAY_AVAILABILITY_TOPIC):
                self.mqtt.publish_event(topic, payload, retain=True)
        Logger().info(f"HomeAssistant : Discovery published for {', '.join(config.DAIKIN_HOSTS)}")

    def poll(self, host):
        with self.lock:
            control = self.daikin._get_control(host)
            sensor = self.daikin.get_sensor(host)
        if not control:
            Logger().warning(f"HomeAssistant : No control info from {host}")
            return
        self.mqtt.publish_event(ha_discovery.state_topic(host), ha_discovery.ha_state(control, sensor), retain=True)

    def handle_command(self, host, field, value):
        if host not in config.DAIKIN_HOSTS:
            Logger().warning(f"HomeAssistant : Command for unknown host {host}, add it to DAIKIN_HOSTS")
            return
        with self.lock:
            control = self.daikin._get_control(host)
            changes = ha_discovery.changes_for_command(field, value, control or {})
            if changes is None:
                Logger().error(f"HomeAssistant : Unsupported command {field}={value!r} for {host}")
                return
            Logger().info(f"HomeAssistant : {host} {field}={value} -> {changes}")
            self.daikin.control_update(host, changes)
        self.poll(host)

    def poll_all(self):
        for host in config.DAIKIN_HOSTS:
            try:
                self.poll(host)
            except Exception as e:
                Logger().error(f"HomeAssistant : Poll of {host} failed: {e}")

    def _poll_loop(self):
        # The first poll runs on connect, see HA_CONNECTED
        while True:
            time.sleep(config.DAIKIN_POLL_INTERVAL)
            self.poll_all()
