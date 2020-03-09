import gc
import esp
esp.osdebug(0)

# Adding in a few here even if they're not called directly to make sure
#   they're always available in an interactive session
import time
import machine
import ubinascii
import ujson as json
from machine import Pin

import utils
import utils_wifi as uwifi
import wemoButton as wemobutt

# Init the stuff
# WiFi Status, cmd status, onboard
# ESP-12 NodeMCU LED is on Pin 2
ledStatus = utils.shinyThing(pin=14)
ledTrigger = utils.shinyThing(pin=16)
ledBuiltin = utils.shinyThing(pin=2, inverted=True)

butt = utils.initButton(12)

ledStatus.on()
ledBuiltin.on()

# This gives time for any automatic wifi connection to finish
time.sleep(5)

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
    ledStatus.off()
else:
    utils.blinken(ledStatus, 0.25, 10)
    ledStatus.on()
# In case you want the MAC address, here it is
macaddr = ubinascii.hexlify(wlan.config('mac'),':').decode()
print("Device MAC:", macaddr)

# Ok, give even a little more time for things to settle before
#   we move on to main.py
time.sleep(2)

# Tidy up before the infinite loop
ledBuiltin.off()
gc.collect()

# At this point, you're ready to go.  Define your specific sensor needs,
#   then import your main loop and call it

# Start the main loop
try:
    wemobutt.looper(knownaps, wlan, conncheck, wconfig,
                    trigger=butt,
                    ledTrigger=ledTrigger,
                    ledStatus=ledStatus,
                    ledBuiltin=ledBuiltin)
except:
    print("Major fail :(")

# Drop the hammer and just reset this goddamn thing
print("Resetting in 5 seconds ...")
time.sleep(5)
machine.reset()
