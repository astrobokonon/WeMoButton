import time
from machine import Pin, PWM, Timer


class shinyThing(object):
    def __init__(self, pin=None, inverted=False, startBlink=True):
        self.pinnum = pin
        self.inverted = inverted

        # Should probably put this in a try...except block?
        self.pin = initLED(self.pinnum)

        if startBlink is True:
            self.on()
            time.sleep(1)
            self.off()

    def on(self):
        """
        Alternate/backup interface to self.pin.on(). Allows me to wrap the
        inversion logic into it so I can always use on() and off().
        """
        if self.inverted is True:
            self.pin.value(0)
        else:
            self.pin.value(1)

    def off(self):
        if self.inverted is True:
            self.pin.value(1)
        else:
            self.pin.value(0)

    def toggle(self):
        self.pin.value(not self.pin.value())


def initButton(pinno):
    """
    """
    print("Setting Pin %02d as INPUT" % (pinno))
    butt = Pin(pinno, Pin.IN, Pin.PULL_UP)

    # I am a simple man.
    return butt


def initLED(pinno):
    """
    """
    # Regular (non-pwm, just on/off)
    print("Setting Pin %02d as OUTPUT" % (pinno))
    led = Pin(pinno, Pin.OUT)

    return led


def blinken(led, duration=0.5, nblinks=1):
    # duration is in seconds
    for _ in range(0, nblinks):
        led.on()
        time.sleep(duration)
        led.off()
        time.sleep(duration)
