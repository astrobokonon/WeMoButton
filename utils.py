import time
from machine import Pin, PWM, Timer


def buttons_init(pins):
    # I am a simple man.
    butts = []
    for pin in pins:
        print("Setting Pin %02d as INPUT" % (pin))
        butt = Pin(pin, Pin.IN, Pin.PULL_UP)
        butts.append(butt)

    return butts


def led_init(pins):
    leds = []
    for i, pinno in enumerate(pins):
        # Regular (non-pwm, just on/off)
        led = Pin(pinno, Pin.OUT)
        led.value(1)
        time.sleep(0.5)
        led.value(0)
        leds.append(led)

    return leds


def blinken(led, duration=0.5, nblinks=1):
    # duration is in seconds
    for i in range(0, nblinks):
        led.value(1)
        time.sleep(duration)
        led.value(0)
        time.sleep(duration)
