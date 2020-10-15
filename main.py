# leds[0] is the button press indicator
# leds[1] is the boot success/wifi indicator
# butts[0] is the button pin object

import gc
import time
import micropython
from machine import Timer

import wemo
import utils
import utils_wifi as uwifi
import utils_requests as ureq


def check_switch(p):
    global triggerButton
    global buttState
    global buttPrevious
    global buttOn
    buttState = triggerButton.value()
    if buttState != buttPrevious:
        buttOn = True

    buttPrevious = buttState


def go(deviceid, config, wlconfig, loops=25):
    """
    Every single board deployment must have this function accepting these
    exact arguments.  Only way to ensure a non-maddening structure!
    """
    # Unpack the things
    knownaps = config['knownaps']
    dbconfig = config['dbconfig']
    wlan = wlconfig['wlan']
    wconfig = wlconfig['wconfig']

    # Init the things
    # WiFi Status, cmd status, onboard
    # ESP-12 NodeMCU LED is on Pin 2
    ledStatus = utils.shinyThing(pin=14)
    ledTrigger = utils.shinyThing(pin=16)
    ledBuiltin = utils.shinyThing(pin=2, inverted=True)
    buttPrevious = None

    # These generally need  to be global to avoid headache of passing args
    #   to the check_switch function
    global triggerButton
    global buttState
    global buttPrevious
    global buttOn

    triggerButton = utils.initButton(12)

    # Use the built-in one for this board to indicate our init status
    ledBuiltin.on()

    # Check the state of the button every (period) ms, using
    #   the check_switch func to actually act/set stuff
    tim = Timer(-1)
    tim.init(period=10, mode=Timer.PERIODIC, callback=check_switch)
    print("Button timer init complete.")

    # Indicate our WiFi connection status
    if wlan.isconnected() is True:
        ledStatus.off()
    else:
        utils.blinken(ledStatus, 0.25, 10)
        ledStatus.on()

    # Capture our starting states
    buttState = triggerButton.value()
    buttPrevious = buttState
    buttOn = False

    # Set up objects
    wemoip = '192.168.1.169'
    validPress = False

    # Timers
    buttTime = None
    wifiTime = None
    wemoTime = None

    # Record the time when we actually break out
    wifiTime = time.ticks_ms()
    checkWiFi = False

    # Set up the basics of the WeMo object. From the above, we should
    #   have a valid wifi connection so go ahead and search for the port
    print("Setting up WeMo control object...")
    wemoObj = wemo.switch(wemoip, portSearch=True, led=ledTrigger)
    wemoTime = time.ticks_ms()
    checkWeMo = False
    print("WeMo object created.")

    # Use the built-in one for this board to indicate our init status
    ledBuiltin.off()

    loopCounter = 0
    while True:
        # If it's been 15 minutes or more, check the wemo state
        #   Split it into this 2-step check to allow for on-demand checks
        if (time.ticks_diff(time.ticks_ms(), wemoTime)) > 900000:
            checkWeMo = True

        # If it's been 1.5 minutes or more, check the wifi status.
        if (time.ticks_diff(time.ticks_ms(), wifiTime)) > 90000:
            checkWiFi = True

        if checkWeMo is True:
            print("Memory info:")
            micropython.mem_info()

            print("Checking WeMo status...")

            # Only do it if the wifi checks out
            if wlan.isconnected() is True:
                port = wemoObj.portSearch(led=ledTrigger)
                print("Port search results: ", port)
                if port != 0:
                    wemoObj.port = port
                    print("WeMo is bueno!")
                else:
                    print("WeMo is no bueno!")
                    wemoObj.port = 0
            else:
                # Force re-check the wifi
                checkWifi = True
                # Then force re-check the WeMo on the next loop
                checkWemo = True

            # Update the time we checked regardless if it was good or bad
            wemoTime = time.ticks_ms()
            checkWeMo = False

        if checkWiFi is True:
            print("Checking WiFi status...")
            wlan, wconfig = uwifi.checkWifiStatus(knownaps,
                                                  wlan=wlan,
                                                  conf=wconfig,
                                                  repl=False)

            if wlan.isconnected() is False:
                # Failed connection attempt! Try to warn
                utils.blinken(ledStatus, 0.25, 5)
            else:
                # Try to store the connection information
                sV = utils.postNetConfig(wlan, dbconfig, tagname=deviceid)

            # Update the time we checked regardless if it was good or bad
            wifiTime = time.ticks_ms()
            checkWiFi = False

        # Check the button state. 'buttOn' is set in the periodic callback
        if buttOn:
            if buttState == 1:
                if buttTime is None:
                    # First time it's been pressed, so that's ok. Mark the time
                    #   for the next comparison and actually do the action
                    buttTime = time.ticks_ms()
                    validPress = True
                else:
                    # Compare now to the previous button press time
                    #   NEED to use ticks_diff() because it has rollover logic!
                    if (time.ticks_diff(time.ticks_ms(), buttTime)) < 1500:
                        # Too soon! Ignore the press
                        validPress = False
                    else:
                        # Do the action
                        validPress = True

                if validPress:
                    print('Button pressed!')
                    print("Current port:", wemoObj.port)
                    if wemoObj.port != 0:
                        ledTrigger.on()
                        wemoObj.toggle()
                        ledTrigger.off()
                        # Since this worked, reset the state checks
                        checkWeMo = False
                        wemoTime = time.ticks_ms()
                    else:
                        print("WeMo is no bueno!")
                        utils.blinken(ledTrigger, 0.1, 7)
                        # Force a re-check of the wemo status
                        checkWeMo = True

                    # Record our time for the next comparison
                    buttTime = time.ticks_ms()
                else:
                    utils.blinken(ledTrigger, 0.25, 3)
            buttOn = False

        # Prepare for the next loop, if there is one left in the hopper
        gc.collect()
        loopCounter += 1

        time.sleep_ms(5)
