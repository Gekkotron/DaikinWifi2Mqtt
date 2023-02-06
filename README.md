# DaikinWifi2Mqtt

To test with fake daikin wifi (minimal support) run "flask --app=server_test run"

To run gateway run "python3 main.py"


Send with mqtt :

# Control all fields :
daikin/192.168.1.150/control      -->    

# Power on
{"key":"pow","value":"1"}
# Power off
{"key":"pow","value":"0"}

# Ventilation Nuit
{"key":"f_rate","value":"B"}
# Ventilation Auto
{"key":"f_rate","value":"A"}
# Ventilation 1
{"key":"f_rate","value":"3"}    
# Ventilation 5
{"key":"f_rate","value":"7"}

# PowerFul mode
daikin/192.168.1.150/powerful     -->     {"status":1,"duration":300}
daikin/192.168.1.150/powerful     -->     {"status":0}


To test in local we can use :
mosquitto_pub -h localhost -t daikin/192.168.1.150/control -m "{\"key\":\"f_rate\",\"value\":\"7\"}"
