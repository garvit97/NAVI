import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(0)

def setupout(pins):
    for pin in pins:
        GPIO.setup(pin,GPIO.OUT)

def on(pins):
    for pin in pins:
        GPIO.output(pin,1)

def off(pins):
    for pin in pins:
        GPIO.output(pin,0)

def setupin(pins,pud):
    for pin in pins:
        if pud==0:
            GPIO.setup(pin,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
        else:
            GPIO.setup(pin,GPIO.IN,pull_up_down=GPIO.PUD_UP)
