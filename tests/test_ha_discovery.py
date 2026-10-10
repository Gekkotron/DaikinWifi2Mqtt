import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import ha_discovery

CONTROL = {
    "ret": "OK", "pow": "1", "mode": "3", "stemp": "25.0", "shum": "0",
    "dt1": "25.0", "dt2": "M", "dt3": "25.0", "dt4": "21.0", "dh2": "50", "dh4": "0",
    "f_rate": "A", "f_dir": "1",
}
SENSOR = {"ret": "OK", "htemp": "24.0", "hhum": "-", "otemp": "-7.0", "err": "0"}


class HaStateTest(unittest.TestCase):
    def test_running_unit(self):
        self.assertEqual(ha_discovery.ha_state(CONTROL, SENSOR), {
            "mode": "cool",
            "target_temperature": 25.0,
            "current_temperature": 24.0,
            "outside_temperature": -7.0,
            "fan_mode": "auto",
            "swing_mode": "vertical",
        })

    def test_powered_off_unit_is_off(self):
        self.assertEqual(ha_discovery.ha_state({**CONTROL, "pow": "0"}, SENSOR)["mode"], "off")

    def test_placeholders_become_none(self):
        state = ha_discovery.ha_state({**CONTROL, "mode": "2", "stemp": "M"}, {"otemp": "-"})
        self.assertEqual(state["mode"], "dry")
        self.assertIsNone(state["target_temperature"])
        self.assertIsNone(state["current_temperature"])
        self.assertIsNone(state["outside_temperature"])


class CommandTest(unittest.TestCase):
    def test_off(self):
        self.assertEqual(ha_discovery.changes_for_command("mode", "off", CONTROL), {"pow": "0"})

    def test_mode_restores_remembered_setpoint(self):
        self.assertEqual(ha_discovery.changes_for_command("mode", "heat", CONTROL),
                         {"pow": "1", "mode": "4", "stemp": "21.0", "shum": "0"})

    def test_fan_only_without_memory(self):
        self.assertEqual(ha_discovery.changes_for_command("mode", "fan_only", CONTROL),
                         {"pow": "1", "mode": "6", "stemp": "0"})

    def test_temperature_is_rounded_and_clamped(self):
        self.assertEqual(ha_discovery.changes_for_command("temperature", "21.3", CONTROL), {"stemp": "21.5"})
        self.assertEqual(ha_discovery.changes_for_command("temperature", "40", CONTROL), {"stemp": "32.0"})

    def test_fan_and_swing(self):
        self.assertEqual(ha_discovery.changes_for_command("fan_mode", "silence", CONTROL), {"f_rate": "B"})
        self.assertEqual(ha_discovery.changes_for_command("fan_mode", "5", CONTROL), {"f_rate": "7"})
        self.assertEqual(ha_discovery.changes_for_command("swing_mode", "both", CONTROL), {"f_dir": "3"})

    def test_unknown_values(self):
        self.assertIsNone(ha_discovery.changes_for_command("mode", "turbo", CONTROL))
        self.assertIsNone(ha_discovery.changes_for_command("temperature", "warm", CONTROL))
        self.assertIsNone(ha_discovery.changes_for_command("preset", "eco", CONTROL))


class DiscoveryTest(unittest.TestCase):
    def test_messages(self):
        messages = dict(ha_discovery.discovery_messages("homeassistant", "192.168.1.150", "Living room", "daikin/bridge/availability"))
        self.assertEqual(set(messages), {
            "homeassistant/climate/daikin_192_168_1_150/climate/config",
            "homeassistant/sensor/daikin_192_168_1_150/current_temperature/config",
            "homeassistant/sensor/daikin_192_168_1_150/outside_temperature/config",
        })
        climate = messages["homeassistant/climate/daikin_192_168_1_150/climate/config"]
        self.assertEqual(climate["device"]["name"], "Living room")
        self.assertEqual(climate["mode_command_topic"], "daikin/192.168.1.150/ha/mode/set")
        self.assertEqual(climate["mode_state_topic"], "daikin/192.168.1.150/ha/state")
        self.assertEqual(climate["availability"], [{"topic": "daikin/bridge/availability"}])
        sensor = messages["homeassistant/sensor/daikin_192_168_1_150/outside_temperature/config"]
        self.assertEqual(sensor["value_template"], "{{ value_json.outside_temperature }}")
        self.assertEqual(sensor["unique_id"], "daikin_192_168_1_150_outside_temperature")

    def test_default_device_name(self):
        topic, climate = ha_discovery.discovery_messages("ha", "10.0.0.2", None, "a")[0]
        self.assertEqual(climate["device"]["name"], "Daikin 10.0.0.2")


class ConfigTest(unittest.TestCase):
    def test_parse_hosts(self):
        self.assertEqual(config.parse_hosts(" 192.168.1.150=Living room, 192.168.1.151 ,,"),
                         {"192.168.1.150": "Living room", "192.168.1.151": None})


if __name__ == "__main__":
    unittest.main()
