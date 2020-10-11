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

try:
    import main
except ImportError:
    main = None


def init():
    """
    This is common to all MicroPython ESP32 (or any WiFi board) startups
    """
    # This gives time for any automatic wifi connection to finish
    time.sleep(5)

    # Define the known access points to try to connect to, and make them global
    #   so the main loop can access them when/if needed
    try:
        with open('./knownaps.json') as f:
            klines = f.read()
        # Tidy up for parsing now
        klines = klines.replace('\n', '')
        knownaps = json.loads(klines)
    except OSError:
        print("knownaps.json file not found!")
        knownaps = None

    # Attempt to connect to one of the strongest of knownaps
    #   If repl is True, start the webrepl too
    wlan, wconfig = uwifi.checkWifiStatus(knownaps, repl=True)

    # In case you want the MAC address, here it is
    macaddr = ubinascii.hexlify(wlan.config('mac'), ':').decode()
    print("Device MAC:", macaddr)

    # Ok, give even a little more time for things to settle before
    #   we move on to main.py
    time.sleep(2)

    # Almost ready for main loop.  Read in the database information first
    try:
        with open('./dbconfig.json') as f:
            dlines = f.read()
        # Tidy up for parsing now
        dlines = dlines.replace('\n', '')
        dbconfig = json.loads(dlines)
    except OSError:
        print("knownaps.json file not found!")
        dbconfig = None

    # Pack up the wireless info so we can pass it around
    wlconfig = {"wlan": wlan,
                "wconfig": wconfig}

    gc.collect()

    return knownaps, dbconfig, wlconfig


if __name__ == "__main__":
    knownaps, dbconfig, wlconfig = init()
    if main is not None:
        if knownaps is not None and dbconfig is not None:
            main.go(knownaps, dbconfig, wlconfig, loops=25)
        else:
            print("WiFi and database configurations are null.")
            print("Aborting main loop start!")
    else:
        print("No main() found!  Is that what you meant to do?")
