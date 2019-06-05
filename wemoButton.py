import gc
import time
from machine import Timer

import utils
import wemo as wemo
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


def checkWiFi():
    pass


def checkWeMo(wemoObj, conncheck, ledTrigger):
    print("Checking WeMo status...")

    # Only do it if the wifi checks out
    if conncheck is True:
        port = wemoObj.portSearch(led=ledTrigger)
        print("Port search results: ", port)
        if port != 0:
            wemoObj.port = port
            print("WeMo is bueno!")
        else:
            print("WeMo is no bueno!")
            wemoObj.port = 0

    # Update the time we checked regardless if it was good or bad
    wemoObj.checkTime = time.ticks_ms()

    return wemoObj


def looper(knownaps, wlan, conncheck, wconfig,
           trigger=None,
           ledTrigger=None, ledStatus=None, ledBuiltin=None):

    # Set up objects
    wemoip = '192.168.1.169'
    # These generally need  to be global to avoid headache of passing arguments
    #   to the check_switch function
    global triggerButton
    triggerButton = trigger
    global buttState
    buttState = triggerButton.value()
    global buttPrevious
    buttPrevious = buttState
    global buttOn
    buttOn = False
    validPress = False

    # Check the state of the button every (period) ms, using
    #   the check_switch func to actually act/set stuff
    tim = Timer(-1)
    tim.init(period=10, mode=Timer.PERIODIC, callback=check_switch)
    print("Button timer init complete.")

    # Timers
    buttTime = None
    wifiTime = None
    wemoTime = None

    # Check the WiFi status before we get started. Actually, don't do anything
    #   else until the WiFi comes back looking ok
    while conncheck is False:
        wlan, conncheck, wconfig = uwifi.checkWifiStatus(knownaps, repl=True)
    print("WiFi established.")

    # Record the time when we actually break out
    wifiTime = time.ticks_ms()
    checkWiFi = False

    # Set up the basics of the WeMo object. From the above, we should
    #   have a valid wifi connection so go ahead and search for the port
    print("Setting up WeMo control object...")
    wemoObj = wemo.switch(wemoip, portSearch=True, led=ledTrigger)
    checkWeMo = False
    print("WeMo object created.")

    while True:
        # If it's been 15 minutes or more, check the wemo state
        #   Split it into this 2-step check to allow for on-demand checks
        if (time.ticks_diff(time.ticks_ms(), wemoObj.checkTime)) > 900000:
            checkWeMo = True

        # If it's been 1.5 minutes or more, check the wifi status.
        if (time.ticks_diff(time.ticks_ms(), wifiTime)) > 90000:
            checkWiFi = True
            # Print out some memory info
            print("Memory info: %d alloc, %d free" % \
                  (gc.mem_alloc(), gc.mem_free()))
            uptime = time.time()
            print("Uptime: %d seconds (%.02f hrs)" % (uptime, uptime/60./60.))

        if checkWeMo is True:
            print("Checking WeMo status...")
            wemoObj = checkWeMo(wemoObj, conncheck, ledTrigger)
            checkWeMo = False

        if checkWiFi is True:
            # Clean up here since this is the shorter/tighter loop
            gc.collect()

            print("Checking WiFi status...")
            # If it's dead, attempt to connect to the strongest of 'knownaps'
            #   NOTE: These should all exist from the first run in boot.py!
            wlan, conncheck, wconfig = uwifi.checkWifiStatus(knownaps,
                                                             wlan=wlan,
                                                             conn=conncheck,
                                                             conf=wconfig,
                                                             repl=True)
            if conncheck is False:
                # Failed connection attempt! Try to warn
                utils.blinken(ledStatus, 0.25, 5)

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

                    # Check to see if the WeMo responds

                    # Try 3 times to actually send the button push command
                    ctries = 0
                    while wemoObj.port == 0 and ctries < 3:
                        print("Checking WeMo status...")
                        wemoObj = checkWeMo(wemoObj, conncheck, ledTrigger)
                        ctries += 1

                    if wemoObj.port != 0:
                        ledTrigger.on()
                        wemoObj.toggle()
                        ledTrigger.off()
                        # Since this worked, reset the state checks
                        checkWeMo = False
                        wemoObj.checkTime = time.ticks_ms()
                    else:
                        print("WeMo is no bueno!")
                        utils.blinken(ledTrigger, 0.1, 7)
                        # Force re-check of the wemo status the next time thru
                        checkWeMo = True


                    # Record our time for the next comparison
                    buttTime = time.ticks_ms()
                else:
                    utils.blinken(ledTrigger, 0.25, 3)
            buttOn = False

        # Ultimate loop time constant
        time.sleep_ms(5)
