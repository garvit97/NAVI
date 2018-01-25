import buzzer
import time
import threading


off=False
pin=[5]
buzzer.setupout(pin)

def create(pw,dutycycle,init):
    global off
    if init==1:
        while True and off==False:
            buzzer.on(pin)
            time.sleep(dutycycle*pw)
            buzzer.off(pin)
            time.sleep((1-dutycycle)*pw)
    else:
        while True and off==False:
            buzzer.off(pin)
            time.sleep((1-dutycycle)*pw)
            buzzer.on(pin)
            time.sleep(dutycycle*pw)
    off=False

def wave(ontime,offtime):
    create(ontime+offtime,ontime/(ontime+offtime),1)

def createpulse(pw,dutycycle,init):
    if init==1:
        buzzer.on(pin)
        time.sleep(dutycycle*pw)
        buzzer.off(pin)
        time.sleep((1-dutycycle)*pw)
    else:
        buzzer.off(pin)
        time.sleep((1-dutycycle)*pw)
        buzzer.on(pin)
        time.sleep(dutycycle*pw)

def infwave(ontime,offtime):
    th=threading.Thread(target=wave,args=(ontime,offtime))
    th.start()

def switchoff():
    global off
    off=True

if __name__=="__main__":
    wave(1,1)
