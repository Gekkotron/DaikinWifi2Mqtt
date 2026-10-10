import os


def _env_bool(name, default):
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def parse_hosts(raw):
    """ "192.168.1.150=Living room,192.168.1.151" -> {"192.168.1.150": "Living room", "192.168.1.151": None} """
    hosts = {}
    for item in raw.split(","):
        host, _, name = item.partition("=")
        if host.strip():
            hosts[host.strip()] = name.strip() or None
    return hosts


MQTT_HOST = os.environ.get("MQTT_HOST", "192.168.1.91")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USERNAME = os.environ.get("MQTT_USERNAME") or None
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD") or None

# Home Assistant MQTT discovery (opt-in). Units listed in DAIKIN_HOSTS are announced and polled.
HA_DISCOVERY_ENABLED = _env_bool("HA_DISCOVERY_ENABLED", False)
HA_DISCOVERY_PREFIX = os.environ.get("HA_DISCOVERY_PREFIX", "homeassistant").strip("/")
DAIKIN_HOSTS = parse_hosts(os.environ.get("DAIKIN_HOSTS", ""))
# Seconds between two polls of every DAIKIN_HOSTS unit (0 disables polling)
DAIKIN_POLL_INTERVAL = int(os.environ.get("DAIKIN_POLL_INTERVAL", "60"))

MQTT_GATEWAY_BASE_TOPIC = "daikin/"
MQTT_GATEWAY_MESSAGE = "message"

MQTT_GATEWAY_STATUS_CMD = MQTT_GATEWAY_BASE_TOPIC + "status"
MQTT_GATEWAY_ERROR_CMD = MQTT_GATEWAY_BASE_TOPIC + "error"

MQTT_GATEWAY_CONTROL_CMD = MQTT_GATEWAY_BASE_TOPIC + "control"
MQTT_GATEWAY_REFRESH_CMD = MQTT_GATEWAY_BASE_TOPIC + "refresh"

MQTT_GATEWAY_CONTROL_RESULT = MQTT_GATEWAY_BASE_TOPIC + "result"
MQTT_GATEWAY_REFRESH_DATA = MQTT_GATEWAY_BASE_TOPIC + "data"
MQTT_GATEWAY_REFRESH_SENSOR = MQTT_GATEWAY_BASE_TOPIC + "sensor"

MQTT_GATEWAY_PUBLISH_TOPIC = MQTT_GATEWAY_BASE_TOPIC + "publish"

# Retained "online"/"offline" ("offline" is also the MQTT last will)
MQTT_GATEWAY_AVAILABILITY_TOPIC = MQTT_GATEWAY_BASE_TOPIC + "bridge/availability"

# Home Assistant events
HA_CONNECTED = "ha_connected"    # broker (re)connected or HA restarted: publish discovery again
HA_COMMAND = "ha_command"        # {"host", "field", "value"} from daikin/<host>/ha/<field>/set

MQTT_GATEWAY_STATUS_START = "start"
MQTT_GATEWAY_STATUS_QUIT = "quit"

#   daikin/refresh      {"host": "http://127.0.0.1:5000"}
