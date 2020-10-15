import time
import urequests
from machine import Pin


def postNetConfig(wlan, dbconfig, tagname="cynomys", debug=True):
    """
    """
    # Quick and early exit
    if wlan.isconnected() is False:
        sV = False
        return sV

    # curIPs: ip, subnet, gateway, dns
    curIPs = wlan.ifconfig()
    curAP = wlan.config('essid')
    curRSSI = wlan.status('rssi')

    if debug is True:
        print("Connected to %s at %s thru %s at %.0f dBm\n" % (curAP,
                                                               curIPs[0],
                                                               curIPs[2],
                                                               curRSSI))

    # We always try at least once, but we check before trying again
    #   Logic is a bit clunky but it'll work.  This makes it so once sV
    #   goes False, it stays False and is returned.  I suppose I could
    #   gather them all up independently and then check but this seemed
    #   a little faster/easier.
    sV = False
    sV = postToInfluxDB(dbconfig, curIPs[0], keyname="ipaddress",
                        tagN=tagname, tagV="network")
    time.sleep(0.25)

    if sV is True:
        sV = postToInfluxDB(dbconfig, curIPs[2], keyname="gateway",
                            tagN=tagname, tagV="network")
        time.sleep(0.25)

    if sV is True:
        sV = postToInfluxDB(dbconfig, curIPs[3], keyname="dns",
                            tagN=tagname, tagV="network")
        time.sleep(0.25)

    if sV is True:
        sV = postToInfluxDB(dbconfig, curAP, keyname="accesspoint",
                            tagN=tagname, tagV="network")
        time.sleep(0.25)

    if sV is True:
        sV = postToInfluxDB(dbconfig, curRSSI, keyname="rssi",
                            tagN=tagname, tagV="network")

    return sV


def postToInfluxDB(dbconfig, value, keyname='value', tagN=None, tagV=None):
    """
    Just using the HTTP endpoint and the simple line protocol.

    Also letting the database time tag it for us.
    """
    host = dbconfig['dbhost']
    port = dbconfig['dbport']
    dbname = dbconfig['dbname']
    metric = dbconfig['dbtabl']

    dbuser = None
    dbpass = None
    try:
        dbuser = dbconfig['dbuser']
    except KeyError:
        # print("No database user found")
        pass

    if dbuser is not None:
        try:
            dbpass = dbconfig['dbpass']
        except KeyError:
            pass
            # print("DB user defined, but no password given!")

    success = False

    if dbuser is not None and dbpass is not None:
        url = "http://%s:%s/write?u=%s&p=%s&db=%s" % (host, port,
                                                      dbuser, dbpass, dbname)
    else:
        url = "http://%s:%s/write?db=%s" % (host, port, dbname)

    print("Using HTTP URL:")
    print(url)

    if (tagN is not None) and (tagV is not None):
        if isinstance(value, float):
            line = '%s,%s=%s %s=%.02f' % (metric, tagN, tagV, keyname, value)
        elif isinstance(value, int):
            line = '%s,%s=%s %s=%d' % (metric, tagN, tagV, keyname, value)
        elif isinstance(value, str):
            line = '%s,%s=%s %s="%s"' % (metric, tagN, tagV, keyname, value)
    else:
        if isinstance(value, float):
            line = '%s %s=%.02f' % (metric, keyname, value)
        if isinstance(value, int):
            line = '%s %s=%d' % (metric, keyname, value)
        elif isinstance(value, str):
            line = '%s %s="%s"' % (metric, keyname, value)

    # There are few rails here so this could go ... poorly.
    try:
        print("Posting to %s:%s %s.%s" % (host, port,
                                          dbname, metric))
        # print("%s=%s, %s=%s" % (tagN, tagV, keyname, value))
        print(url)
        print(line)
        response = urequests.post(url, data=line)
        print("Response:", response.status_code, response.text)
        success = True
    except OSError as e:
        print(str(e))
    except Exception as e:
        print(str(e))

    return success


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
