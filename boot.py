# This file is executed on every boot (including wake-boot from deepsleep)
import esp
esp.osdebug(0)

# Adding in a few here even if they're not called directly to make sure
#   they're always available in an interactive session
import os
import time
import network
import webrepl
import ubinascii
import ujson as json
from machine import Pin, PWM, Timer

import utils
import utils_wifi as uwifi
import wemoButton as wemobutt


# Init the stuff
# WiFi Status, cmd status, onboard
# ESP-12 NodeMCU LED is on Pin 2...?
leds = utils.led_init([2, 5, 4])
butts = utils.buttons_init([14])
time.sleep(3)

# Define the known access points to try to connect to, and make them global
#   so the main loop can access them when/if needed
with open('./knownaps.json') as f:
    klines = f.read()
# Tidy up for parsing now
klines = klines.replace('\n', '')
knownaps = json.loads(klines)

# Attempt to connect to one of the strongest of knownaps
#   If repl is True, start the webrepl too
wlan, conncheck, wconfig = uwifi.checkWifiStatus(knownaps, repl=True)

if conncheck is True:
    leds[0].value(0)
else:
    utils.blinken(leds[0], 0.25, 10)
    leds[0].value(1)

# In case you want the MAC address, here it is in two parts
# macaddr = ubinascii.hexlify(wlan.config('mac'),':').decode()
# mac1 = macaddr[0:8]
# mac2 = macaddr[8:]

# Ok, give even a little more time for things to settle before
#   we move on to main.py
time.sleep(2)

# Start the main loop
wemobutt.looper(knownaps, wlan, conncheck, wconfig, leds, butts)
