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

    # The (json) config file should have 3 sections:
    #   "name": (device/nodeid here)
    #   "knownaps": (dict of ssid/passwords)
    #   "dbconfig": (influxdb information)
    try:
        with open('./config.json') as f:
            klines = f.read()
        # Tidy up for parsing now
        klines = klines.replace('\n', '')
        config = json.loads(klines)
    except OSError:
        print("config.json file not found!")
        config = None

    # Now try to pull out the bits in the config that SHOULD be in there
    if config is not None:
        try:
            deviceid = config['deviceid']
        except KeyError:
            deviceid = "UndefinedCynomys"

        try:
            knownaps = config['knownaps']
        except KeyError:
            print("No wifi configuration found!")
            knownaps = None

        try:
            dbconfig = config['dbconfig']
        except KeyError:
            print("No database configuration found!")
            dbconfig = None

    # Attempt to connect to one of the strongest of knownaps
    #   If repl is True, start the webrepl too
    wlan, wconfig = uwifi.checkWifiStatus(knownaps, repl=True)

    # In case you want the MAC address, here it is
    macaddr = ubinascii.hexlify(wlan.config('mac'), ':').decode()
    print("Device MAC:", macaddr)

    # Ok, give even a little more time for things to settle before
    #   we move on to main.py
    time.sleep(2)

    # Pack up the wireless info so we can pass it around
    wlconfig = {"wlan": wlan,
                "wconfig": wconfig}

    gc.collect()

    return config, wlconfig


if __name__ == "__main__":
    config, wlconfig = init()
    deviceid = config['deviceid']

    if main is not None:
        if config['knownaps'] is not None and config['dbconfig'] is not None:
            main.go(deviceid, config, wlconfig, loops=25)
        else:
            print("WiFi and database configurations are null.")
            print("Aborting main loop start!")
    else:
        print("No main() found!  Is that what you meant to do?")
