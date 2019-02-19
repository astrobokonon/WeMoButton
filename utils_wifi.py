import time
import webrepl
import network


def scanWiFi(wlan):
    try:
        nearbyaps = wlan.scan()
    except OSError as oe:
        # Sometimes we get an "Wifi Invalid Argument" here
        nearbyaps = []

    return nearbyaps


def startWiFi(disableAP=True):
    # Start/restart the wifi
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if disableAP is True:
        # DISABLE the self-hosted access point
        ap_if = network.WLAN(network.AP_IF)
        ap_if.active(False)

    return wlan


def checkAPs(wlan, knownaps, nearbyaps):
    # Check to see if any match
    found = []
    strongest = -10000
    bestssid = None

    print("Found the following access points:")
    for each in nearbyaps:
        # Check for the wifi access points we know about
        for ap in knownaps.keys():
            if ap == each[0].decode("UTF-8"):
                # Store the name and the signal strength
                found.append([ap, each[3]])
                outmsg = "Name: %s\tSignalStrength: %d" % (ap, each[3])
                print(outmsg)
                time.sleep(1.5)
                # Compare current signal strength to our best one
                if each[3] >= strongest:
                    strongest = each[3]
                    bestssid = each[0].decode("UTF-8")

    return found, bestssid, strongest


def connectWiFi(wlan, ssid, rssi, password):
    print("Connecting to %s with signal strength of %d dB..." % (ssid,
                                                                 rssi))
    wlan.connect(ssid, password)
    # Give a healthy amount of time for the connection to finish
    time.sleep(5)

    # Check to see if we're done yet, using these as flags
    tries = 0
    conncheck = False

    while conncheck is False:
        print("Connecting...")
        conncheck = wlan.isconnected()
        time.sleep(1)

        tries += 1
        # while loop escape hatch
        if tries > 10:
            print("Connection timed out! Still might happen though...")
            time.sleep(5)
            break

    if conncheck is True:
        print("Connected!")
        wconfig = wlan.ifconfig()
        print("Current IP: %s" % (wconfig[0]))
    else:
        print("Failed to connect!")
        wconfig = None

    return conncheck, wconfig


def get_RSSI(wlan, ssid):
    nearby = wlan.scan()
    rssi = -99999
    for each in nearby:
        if ssid == each[0].decode("UTF-8"):
            rssi = each[3]

    return rssi


def checkWifiStatus(knownaps, wlan=None, conn=None, conf=None, repl=True):
    if (wlan is None) or (wlan.isconnected()) is False:
        print("WiFi is no bueno!")
        # Redo!
        wlan = startWiFi()
        nearbyaps = scanWiFi(wlan)

        # returns ssid's found, strongest ssid name, and strongest's rssi
        _, bestssid, strongest = checkAPs(wlan, knownaps, nearbyaps)

        conn = False
        if bestssid is not None:
            # Attempt to actually connect
            conn, conf = connectWiFi(wlan, bestssid,
                                     strongest,
                                     knownaps[bestssid])
            if repl is True:
                webrepl.stop()
                time.sleep(0.5)
                webrepl.start()
        else:
            print("No Known Access Point Found!")
    else:
        print("WiFi is bueno!")

    return wlan, conn, conf
