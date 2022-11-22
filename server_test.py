from flask import Flask
from flask import request
import time


app = Flask(__name__)

@app.route('/aircon/get_control_info')
def get_control_info():
    return f"ret=OK,pow={flaskApp.pow},mode={flaskApp.mode},adv={flaskApp.adv},stemp=21.0,shum=0,dt1=25.0,dt2=M,dt3=25.0,dt4=21.0,dt5=21.0,dt7=25.0,dh1=AUTO,dh2=50,dh3=0,dh4=0,dh5=0,dh7=AUTO,dhh=50,b_mode=4,b_stemp=21.0,b_shum=0,alert=255,f_rate=A,f_dir=0,b_f_rate=A,b_f_dir=0,dfr1=5,dfr2=5,dfr3=5,dfr4=A,dfr5=A,dfr6=5,dfr7=5,dfrh=5,dfd1=0,dfd2=0,dfd3=0,dfd4=0,dfd5=0,dfd6=0,dfd7=0,dfdh=0"


@app.route('/aircon/set_control_info')
def set_control_info():
    if(request.args.get('pow') is not None):
        flaskApp.pow = request.args.get('pow')

    if(request.args.get('mode') is not None):
        flaskApp.mode = request.args.get('mode')

    if(request.args.get('adv') is not None):
        flaskApp.adv = request.args.get('adv')

    print(f"set_control_info:pow={flaskApp.pow},mode={flaskApp.mode},adv={flaskApp.adv}")
    return ""


class FlaskApp:
    def __init__(self):
        self.pow = 0
        self.mode = 0
        self.adv = None

flaskApp = FlaskApp()

if __name__ == "__main__":
    while(True):
        time.sleep(0.1)
