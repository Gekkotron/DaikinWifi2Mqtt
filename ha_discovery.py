"""
Home Assistant MQTT discovery for Daikin Wi-Fi units.

Pure functions only (no MQTT, no HTTP) so they can be unit tested:
- discovery_messages(): the retained config payloads announcing one unit
- ha_state(): Daikin control + sensor info -> JSON state published on daikin/<host>/ha/state
- changes_for_command(): an HA command -> the Daikin control fields to send
"""
import re

# Daikin "mode" -> HA hvac mode ("pow" = "0" means off whatever the mode)
DAIKIN_TO_HA_MODE = {"0": "auto", "1": "auto", "7": "auto", "2": "dry", "3": "cool", "4": "heat", "6": "fan_only"}
HA_TO_DAIKIN_MODE = {"auto": "1", "dry": "2", "cool": "3", "heat": "4", "fan_only": "6"}
HA_MODES = ["off", "auto", "cool", "heat", "dry", "fan_only"]

DAIKIN_TO_HA_FAN = {"A": "auto", "B": "silence", "3": "1", "4": "2", "5": "3", "6": "4", "7": "5"}
HA_TO_DAIKIN_FAN = {v: k for k, v in DAIKIN_TO_HA_FAN.items()}

DAIKIN_TO_HA_SWING = {"0": "off", "1": "vertical", "2": "horizontal", "3": "both"}
HA_TO_DAIKIN_SWING = {v: k for k, v in DAIKIN_TO_HA_SWING.items()}

MIN_TEMP = 10
MAX_TEMP = 32

COMMAND_FIELDS = ("mode", "temperature", "fan_mode", "swing_mode")


def unit_id(host):
    return "daikin_" + re.sub(r"[^0-9A-Za-z]+", "_", host).strip("_").lower()


def state_topic(host):
    return f"daikin/{host}/ha/state"


def command_topic(host, field):
    return f"daikin/{host}/ha/{field}/set"


def _temperature(value):
    """ "24.0" -> 24.0, "-" / "--" / "M" / None -> None """
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def ha_state(control, sensor):
    control = control or {}
    sensor = sensor or {}
    if control.get("pow") == "0":
        mode = "off"
    else:
        mode = DAIKIN_TO_HA_MODE.get(control.get("mode"))
    return {
        "mode": mode,
        "target_temperature": _temperature(control.get("stemp")),
        "current_temperature": _temperature(sensor.get("htemp")),
        "outside_temperature": _temperature(sensor.get("otemp")),
        "fan_mode": DAIKIN_TO_HA_FAN.get(control.get("f_rate")),
        "swing_mode": DAIKIN_TO_HA_SWING.get(control.get("f_dir")),
    }


def changes_for_command(field, value, control):
    """
    Returns the Daikin control fields to change, or None when the command is not understood.
    `control` is the unit's current control info, used to restore the setpoint remembered per mode.
    """
    value = value.strip()
    if field == "mode":
        if value == "off":
            return {"pow": "0"}
        mode = HA_TO_DAIKIN_MODE.get(value)
        if mode is None:
            return None
        changes = {"pow": "1", "mode": mode}
        # The unit remembers one setpoint per mode in dt<mode>/dh<mode>
        if control.get("dt" + mode) is not None:
            changes["stemp"] = control["dt" + mode]
        elif mode == "6":
            changes["stemp"] = "0"
        if control.get("dh" + mode) is not None:
            changes["shum"] = control["dh" + mode]
        return changes
    if field == "temperature":
        temperature = _temperature(value)
        if temperature is None:
            return None
        temperature = min(max(temperature, MIN_TEMP), MAX_TEMP)
        return {"stemp": f"{round(temperature * 2) / 2:.1f}"}
    if field == "fan_mode":
        rate = HA_TO_DAIKIN_FAN.get(value)
        return {"f_rate": rate} if rate is not None else None
    if field == "swing_mode":
        direction = HA_TO_DAIKIN_SWING.get(value)
        return {"f_dir": direction} if direction is not None else None
    return None


def discovery_messages(prefix, host, name, availability_topic):
    """ [(topic, payload)] announcing one unit: a climate entity plus inside/outside temperature sensors """
    uid = unit_id(host)
    state = state_topic(host)
    device = {
        "identifiers": [uid],
        "name": name or f"Daikin {host}",
        "manufacturer": "Daikin",
        "model": "Wi-Fi air conditioner",
        "configuration_url": f"http://{host}",
    }
    availability = [{"topic": availability_topic}]

    climate = {
        "name": None,
        "unique_id": uid,
        "object_id": uid,
        "device": device,
        "availability": availability,
        "modes": HA_MODES,
        "fan_modes": list(DAIKIN_TO_HA_FAN.values()),
        "swing_modes": list(DAIKIN_TO_HA_SWING.values()),
        "min_temp": MIN_TEMP,
        "max_temp": MAX_TEMP,
        "temp_step": 0.5,
        "precision": 0.5,
        "temperature_unit": "C",
        "mode_state_topic": state,
        "mode_state_template": "{{ value_json.mode }}",
        "mode_command_topic": command_topic(host, "mode"),
        "temperature_state_topic": state,
        "temperature_state_template": "{{ value_json.target_temperature }}",
        "temperature_command_topic": command_topic(host, "temperature"),
        "current_temperature_topic": state,
        "current_temperature_template": "{{ value_json.current_temperature }}",
        "fan_mode_state_topic": state,
        "fan_mode_state_template": "{{ value_json.fan_mode }}",
        "fan_mode_command_topic": command_topic(host, "fan_mode"),
        "swing_mode_state_topic": state,
        "swing_mode_state_template": "{{ value_json.swing_mode }}",
        "swing_mode_command_topic": command_topic(host, "swing_mode"),
    }

    def temperature_sensor(key, label):
        return {
            "name": label,
            "unique_id": f"{uid}_{key}",
            "object_id": f"{uid}_{key}",
            "device": device,
            "availability": availability,
            "state_topic": state,
            "value_template": f"{{{{ value_json.{key} }}}}",
            "device_class": "temperature",
            "state_class": "measurement",
            "unit_of_measurement": "°C",
        }

    return [
        (f"{prefix}/climate/{uid}/climate/config", climate),
        (f"{prefix}/sensor/{uid}/current_temperature/config", temperature_sensor("current_temperature", "Inside temperature")),
        (f"{prefix}/sensor/{uid}/outside_temperature/config", temperature_sensor("outside_temperature", "Outside temperature")),
    ]
