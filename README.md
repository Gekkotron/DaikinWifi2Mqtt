
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
- `daikin/192.168.1.150/basic` (basic info)

### Local test example
```
mosquitto_pub -h localhost -t daikin/192.168.1.150/control -m '{"key":"f_rate","value":"7"}'
```
