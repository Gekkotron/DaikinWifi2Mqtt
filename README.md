
# DaikinWifi2Mqtt

To test with fake daikin wifi (minimal support) run:
```
flask --app=server_test run
```

To run the gateway:
```
python3 main.py
```

## Docker Usage

You can run DaikinWifi2Mqtt using Docker. There are two options:

### 1. Using Dockerfile

Build the Docker image:

```sh
docker build -t daikinwifi2mqtt .
```

Run the container:

```sh
docker run --rm -it -p 8080:8080 daikinwifi2mqtt
```

Adjust the port mapping as needed for your setup.

### 2. Using Docker Compose

Start the service with Docker Compose:

```sh
docker-compose up --build
```

This will build and start the service as defined in `docker-compose.yml`.

You can stop the service with:

```sh
docker-compose down
```

Make sure to configure environment variables and volumes as needed in the compose file.

### 3. Keeping it updated (`update.sh`)

```sh
./update.sh
```

It runs `git pull --rebase`, then rebuilds and restarts the container only when new commits arrived or the container isn't running (so it also works as a first launch, or from cron). It prunes dangling images and prints the last 30 log lines.

## Configuration

Settings come from environment variables (copy `.env.example` to `.env` for Docker Compose):

| Variable | Default | Description |
|---|---|---|
| `MQTT_HOST` | `192.168.1.91` | Broker host |
| `MQTT_PORT` | `1883` | Broker port |
| `MQTT_USERNAME` | _(empty)_ | Broker login; leave empty for an anonymous broker |
| `MQTT_PASSWORD` | _(empty)_ | Broker password |
| `HA_DISCOVERY_ENABLED` | `false` | Publish Home Assistant MQTT discovery for `DAIKIN_HOSTS` |
| `HA_DISCOVERY_PREFIX` | `homeassistant` | Discovery prefix |
| `DAIKIN_HOSTS` | _(empty)_ | Units to announce, e.g. `192.168.1.150=Living room,192.168.1.151` |
| `DAIKIN_POLL_INTERVAL` | `60` | Seconds between two state polls of `DAIKIN_HOSTS` (`0` = off) |

The bridge publishes a retained `online` on `daikin/bridge/availability` and sets `offline` as its last will.

## Home Assistant discovery

With `HA_DISCOVERY_ENABLED=true`, each unit of `DAIKIN_HOSTS` is announced as one device with:
- a `climate` entity: modes `off/auto/cool/heat/dry/fan_only`, target temperature (10–32 °C, 0.5 step), fan modes `auto/silence/1…5`, swing modes `off/vertical/horizontal/both`
- `Inside temperature` and `Outside temperature` sensors

Configs are retained under `<prefix>/climate|sensor/daikin_<host>/…/config` and published again when the bridge reconnects or Home Assistant sends `online` on `<prefix>/status`.

State is one retained JSON polled every `DAIKIN_POLL_INTERVAL` seconds and after every HA command:
```
daikin/192.168.1.150/ha/state
{"mode": "cool", "target_temperature": 25.0, "current_temperature": 24.0, "outside_temperature": -7.0, "fan_mode": "auto", "swing_mode": "off"}
```
Commands take plain payloads on `daikin/<host>/ha/<mode|temperature|fan_mode|swing_mode>/set`:
```
mosquitto_pub -h localhost -t daikin/192.168.1.150/ha/mode/set -m heat
mosquitto_pub -h localhost -t daikin/192.168.1.150/ha/temperature/set -m 21.5
```
Switching mode restores the setpoint the unit remembers for that mode. The legacy JSON topics below keep working.

Unit tests: `python3 -m unittest discover -s tests`

## MQTT Usage

### Control Example
Send to:
```
daikin/192.168.1.150/control
```
Payloads:
- Power on: `{ "key": "pow", "value": "1" }`
- Power off: `{ "key": "pow", "value": "0" }`
- Ventilation Nuit: `{ "key": "f_rate", "value": "B" }`
- Ventilation Auto: `{ "key": "f_rate", "value": "A" }`
- Ventilation 1: `{ "key": "f_rate", "value": "3" }`
- Ventilation 5: `{ "key": "f_rate", "value": "7" }`

### Powerful Mode
Send to:
```
daikin/192.168.1.150/powerful
```
Payloads:
- Enable: `{ "status": 1, "duration": 300 }`
- Disable: `{ "status": 0 }`

### Refresh (returns control, sensor, and basic info)
Send to:
```
daikin/192.168.1.150/refresh
```
Payload:
```
{ "data": "" }
```
This will return:
- `daikin/192.168.1.150/data` (control info)
- `daikin/192.168.1.150/sensor` (sensor info)
- `daikin/192.168.1.150/status` (basic info)

### Local test example
```
mosquitto_pub -h localhost -t daikin/192.168.1.150/control -m '{"key":"f_rate","value":"7"}'
```
