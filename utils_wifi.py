import time
import webrepl
import network
import ubinascii


def scanWiFi(wlan):
    try:
        # Needed because if you're connected, or trying to connect, 
        #   you'll get this "STA is connecting, scan are not allowed!" 
        wlan.disconnect()
        nearbyaps = wlan.scan()
    except OSError as oe:
        print(str(oe))
        # Sometimes we get an "Wifi Invalid Argument" here
        nearbyaps = []

    return nearbyaps, wlan


def startWiFi(disableAP=True):
    # Start/restart the wifi
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if disableAP is True:
        # DISABLE the self-hosted access point
        ap_if = network.WLAN(network.AP_IF)
        ap_if.active(False)

    return wlan


def checkAPList(knownaps, nearbyaps):
    # Check to see if any match
    strongest = -10000
    bestAP = {}

    print("Found the following access points:")
    for eachAP in nearbyaps:
        # Check for the wifi access points we know about
        for ap in knownaps.keys():
            # Decode the parts
            #   (ssid, bssid, channel, RSSI, authmode, hidden)
            thisAPName = eachAP[0].decode("UTF-8")
            thisAPMAC = ubinascii.hexlify(eachAP[1], ':').decode()
            thisBinMAC = eachAP[1]
            try:
                thisAPChan = int(eachAP[2])
            except ValueError:
                print("Warning: Error converting %s to int!" % (eachAP[2]))
                thisAPChan = -9999
            thisAPRSSI = int(eachAP[3])

            if ap == thisAPName:
                # Store the name and the signal strength
                # found.append([thisAPName, thisAPMAC, thisAPChan, thisAPRSSI])
                outmsg = "%s (%s, %s)" % (ap, thisAPMAC, thisAPChan)
                outmsg += "\t%d dBm" % (thisAPRSSI)
                print(outmsg)
                time.sleep(1.5)
                # Compare current signal strength to our best one
                if thisAPRSSI >= strongest:
                    bestAP = {'ssid': thisAPName,
                              'mac': thisAPMAC,
                              'binmac': thisBinMAC,
                              'rssi': thisAPRSSI}

                    # Store the winning value for next time
                    strongest = thisAPRSSI

    return bestAP


def connectWiFi(wlan, bestAP, password):
    ssid = bestAP['ssid']

    mac = bestAP['mac']
    binmac = bestAP['binmac']
    rssi = bestAP['rssi']
    print("Connecting to %s (%s) with signal strength of %d dB" % (ssid, mac,
                                                                   rssi))

    # Make sure we don't have any lingering connection attemps going on
    wlan.disconnect()
    # The documentation sucks, but bssid should *not* be the string
    #   version of the desired MAC address
    wlan.connect(ssid, password, bssid=binmac)

    # Give a healthy amount of time for the connection to finish
    time.sleep(5)

    # Keep a count on how many times we've tried
    tries = 0

    while wlan.isconnected() is False:
        print("Connecting...")
        conncheck = wlan.isconnected()
        time.sleep(1)

        tries += 1
        # while loop escape hatch
        if tries > 10:
            print("Connection timed out! Still might happen though...")
            time.sleep(5)
            break

    if wlan.isconnected() is True:
        print("Connected!")
        wconfig = wlan.ifconfig()
        print("Current IP: %s" % (wconfig[0]))
    else:
        print("Failed to connect!")
        wconfig = None

    return wconfig


def get_APInfo(wlan, ssid):
    nearby = wlan.scan()
    rssi = -99999
    for each in nearby:
        if ssid == each[0].decode("UTF-8"):
            bssid = each[1]
            channel = each[2]
            rssi = each[3]

    return bssid, channel, rssi


def checkWifiStatus(knownaps, wlan=None, conf=None, repl=True):
    """
    """
    badWifi = False

    # Check on the state of some things to see if we're really connected
    if (wlan is None) or (wlan.isconnected()) is False:
        badWifi = True
    else:
        # The board thinks we're connected, but it might be confused.
        #   There might be a few different fail cases that end up here.

        # DHCP likely expired and didn't renew
        if wlan.ifconfig()[0] == "0.0.0.0":
            badWifi = True

    if badWifi is True:
        print("WiFi is no bueno!")
        # Redo!
        wlan = startWiFi()
        nearbyaps, wlan = scanWiFi(wlan)

        bestAP = None
        bestssid = None
        if knownaps is not None:
            bestAP = checkAPList(knownaps, nearbyaps)
            if bestAP != {}:
                bestssid = bestAP['ssid']

        if bestssid is not None:
            # Attempt to actually connect
            conf = connectWiFi(wlan, bestAP, knownaps[bestssid])
            if repl is True:
                webrepl.stop()
                time.sleep(0.5)
                webrepl.start()
        else:
            print("No Known Access Point Found!")
    else:
        print("WiFi is bueno!")

    return wlan, conf
