import config
from Logger import Logger
import urllib.parse
from Events import Events
import json
import threading
import requests


class Daikin:
    def __init__(self):
        broker = Events().broker
        self.t = None

        @broker.on(config.MQTT_GATEWAY_MESSAGE)
        def message(data):
            topic = data["topic"].split("/")
            host = topic[1]
            cmd = topic[2]
            data["host"] = host

            if("control" in cmd):
                response = self._control_set(data)
                Events().broker.emit(config.MQTT_GATEWAY_PUBLISH_TOPIC, {"topic": "daikin/"+host+"/data", "response": response})
            if("refresh" in cmd):
                response = self._get_control(host)
                Events().broker.emit(config.MQTT_GATEWAY_PUBLISH_TOPIC, {"topic": "daikin/"+host+"/data", "response": response})
                result = self.get_sensor(host)
                Events().broker.emit(config.MQTT_GATEWAY_PUBLISH_TOPIC, {"topic": "daikin/"+host+"/sensor", "response": result})
            if("powerful" in cmd):
                status = data["status"]
                if("duration" in data):
                    duration = data["duration"]
                    if(self.t is not None):
                       self.t.cancel()
                    self.t = threading.Timer(duration, launchPowerfulMode, [host, 0])
                    self.t.start()
                launchPowerfulMode(host, status)

        def launchPowerfulMode(host, status):
            self.powerfulMode(host, status)
            response = self._get_control(host)
            Events().broker.emit(config.MQTT_GATEWAY_PUBLISH_TOPIC, {"topic": "daikin/"+host+"/data", "response": response})

        @broker.on(config.MQTT_GATEWAY_CONTROL_CMD)
        def control(data):
            response = self._control_set(data)
            Events().broker.emit(config.MQTT_GATEWAY_PUBLISH_TOPIC, {"topic": config.MQTT_GATEWAY_REFRESH_DATA, "response": response})

        @broker.on(config.MQTT_GATEWAY_REFRESH_CMD)
        def refresh(payload):
            host = payload["host"]
            response = self._get_control(host)
            Events().broker.emit(config.MQTT_GATEWAY_PUBLISH_TOPIC, {"topic": config.MQTT_GATEWAY_REFRESH_DATA, "response": response})
            result = self.get_sensor(host)
            Events().broker.emit(config.MQTT_GATEWAY_PUBLISH_TOPIC, {"topic": config.MQTT_GATEWAY_REFRESH_SENSOR, "response": result})

    def _get(self, host, path):
        """ Internal function to connect to and get any information"""
        fields = {}
        try:
            response = requests.get("http://" + host + path)
            response.raise_for_status()
            if not len(response.text) > 0 or not response.text[0:4] == "ret=":
                return None

            for group in response.text.split(","):
                element = group.split("=")
                if element[0] == "name":
                    fields[element[0]] = urllib.parse.unquote(element[1])
                else:
                    fields[element[0]] = element[1]

        except requests.exceptions.RequestException as e:  # This is the correct syntax
            Events().broker.emit(config.MQTT_GATEWAY_ERROR_CMD, e)
        return fields

    def _set(self, host, path, data):
        """ Internal function to connect to and update information"""
        try:
            print("SET : " + host + path + str(data))
            response = requests.get("http://" + host + path, data)
            response.raise_for_status()
            return response.json
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            Events().broker.emit(config.MQTT_GATEWAY_ERROR_CMD, e)
        return {}

    def get_basic(self, host):
        """
        Example information:
        ret=OK,type=aircon,reg=eu,dst=1,ver=1_2_51,rev=D3A0C9F,pow=1,err=0,location=0,
        name=%79%6c%c3%a4%61%75%6c%61,icon=0,method=home only,port=30050,id=,pw=,
        lpw_flag=0,adp_kind=3,pv=2,cpv=2,cpv_minor=00,led=1,en_setzone=1,
        mac=D0C5D3042E82,adp_mode=run,en_hol=0,grp_name=,en_grp=0
        :return: dict
        """
        return self._get(host, "/common/basic_info")

    def _get_notify(self, host):
        """
        Example:
        ret=OK,auto_off_flg=0,auto_off_tm=- -
        :return: dict
        """
        return self._get(host, "/common/get_notify")

    def _get_week(self, host):
        """
        Example:
        ret=OK,today_runtime=601,datas=0/0/0/0/0/0/1000
        :return: dict
        """
        return self._get(host, "/aircon/get_week_power")

    def _get_year(self, host):
        """
        Example:
        ret=OK,previous_year=0/0/0/0/0/0/0/0/0/0/0/0,this_year=0/0/0/1
        :return: dict
        """
        return self._get(host, "/aircon/get_year_power")

    def _get_target(self, host):
        """
        Example:
        ret=OK,target=0
        :return: dict
        """
        return self._get(host, "/aircon/get_target")

    def _get_price(self, host):
        """
        Example:
        ret=OK,price_int=27,price_dec=0
        :return: dict
        """
        return self._get(host, "/aircon/get_price")

    def get_sensor(self, host):
        """
        Example:
        ret=OK,htemp=24.0,hhum=-,otemp=-7.0,err=0,cmpfreq=40
        :return: dict
        """
        return self._get(host, "/aircon/get_sensor_info")

    def _get_control(self, host):
        """
        Example:
        ret=OK,pow=1,mode=4,adv=,stemp=21.0,shum=0,dt1=25.0,dt2=M,dt3=25.0,dt4=21.0,
        dt5=21.0,dt7=25.0,dh1=AUTO,dh2=50,dh3=0,dh4=0,dh5=0,dh7=AUTO,dhh=50,b_mode=4,
        b_stemp=21.0,b_shum=0,alert=255,f_rate=A,f_dir=0,b_f_rate=A,b_f_dir=0,dfr1=5,
        dfr2=5,dfr3=5,dfr4=A,dfr5=A,dfr6=5,dfr7=5,dfrh=5,dfd1=0,dfd2=0,dfd3=0,dfd4=0,
        dfd5=0,dfd6=0,dfd7=0,dfdh=0
        :param all_fields: return all fields or just the most relevant f_dir, f_rate,
        mode, pow, shum,
        stemp
        :return: dict

        pow:
        unit on/off
        :return: "1" for ON, "0" for OFF

        stemp:
        target temperature
        range of accepted values determined by mode: AUTO:18-31, HOT:10-31, COLD:18-33
        :return: degrees centigrade

        shum:
        target humidity
        :return: 0

        f_dir:
        horizontal/vertical fan wings motion
        :return: "0":"all wings stopped", "1":"vertical wings motion",
        "2":"horizontal wings motion", "3":"vertical and horizontal wings motion"

        f_rate:
        fan speed
        :return: "A":"auto", "B":"silence", "3":"fan level 1","4":"fan level 2",
        "5":"fan level 3", "6":"fan level 4","7":"fan level 5"

        mode:
        operation mode
        :return: "0": "AUTO", "1": "AUTO", "2": "DEHUMIDIFICATOR", "3": "COLD",
        "4": "HOT", "6": "FAN", "7": "AUTO"
        """
        return self._get(host, "/aircon/get_control_info")

    def _get_model(self, host):
        """
        Example:
        ret=OK,model=0ABB,type=N,pv=2,cpv=2,cpv_minor=00,mid=NA,humd=0,s_humd=0,
        acled=0,land=0,elec=0,temp=1,temp_rng=0,m_dtct=1,ac_dst=--,disp_dry=0,dmnd=0,
        en_scdltmr=1,en_frate=1,en_fdir=1,s_fdir=3,en_rtemp_a=0,en_spmode=0,
        en_ipw_sep=0,en_mompow=0
        :return: dict
        """
        return self._get(host, "/aircon/get_model_info")

    def _get_remote(self, host):
        """
        Example:
        ret=OK,method=home only,notice_ip_int=3600,notice_sync_int=60
        :return: dict
        """
        return self._get(host, "/common/get_remote_method")

    def _control_set(self, payload):
        if "host" not in payload:
            return {}

        """
        set a get_control() item via one of the property.setters

        will fetch the current settings to change this one value, so this is not safe
        against concurrent changes
        :param key: item name e.g. "pow"
        :param value: set to value e.g. 1, "1" or "ON"
        :return: None
        """
        host = payload["host"]
        data = self._get_control(host)
        data[payload["key"]] = payload["value"]

        if payload["value"] == "6":
            data["stemp"] = "0"
        elif data["stemp"] == "--":
            # If the current setpoint is 0, set it at default
            data["stemp"] = 18
            data["shum"] = 0
            print("Update to default value")
        self._set(host, "/aircon/set_control_info", data)
        return data

    def powerfulMode(self, host, status):
        data={}
        data["spmode_kind"] = 1
        data["set_spmode"] = status
        self._set(host, f"/aircon/set_special_mode", data)
