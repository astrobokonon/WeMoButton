"""An easy way to integrate wemo switches

Inspired by https://github.com/DocCodes/wemo

...But that version was totally broken for me. Also
had to remove f-strings for adaptation for MicroPython.

The check() method was just borked; it kept thinking the right port
was 49155 when the right answer was 49153, so I redid it to try actual
status requests and see which one *didn't* error out.
"""

import time

import utils

try:
    # from urequests import get, post
    from utils_requests import get, post
except ImportError as ie:
    from requests import get, post


class switch:
    def __init__(self, ip, portSearch=True, led=None):
        self.ip = ip
        self.port = 0
        self.service = '/upnp/control/basicevent1'
        self.full = None
        self.url = None
        self.state = None
        self.name = None
        self.checkTime = None

        # Search for the right port; can be re-called to verify later
        if portSearch is True:
            self.port = self.portSearch(led=led)
        else:
            self.port = 0

        # If we found a port get the rest of the info
        if self.port > 0:
            print("Getting state %s" % (self.url))
            self.state = self.checkState()

            print("Getting name %s" % (self.url))
            self.name = self.getFunc('GetFriendlyName', 'FriendlyName')

    def checkState(self):
        stat = self.getFunc('GetBinaryState', 'BinaryState')
        if stat is not None:
            try:
                state = int(stat)
            except ValueError as ve:
                state = stat
        else:
            print("STATUS QUERY FAILED!!!")
            state = None

        return state

    def enable(self):
        resp = self.setFunc('SetBinaryState', 'BinaryState', 1)
        self.state = resp

    def disable(self):
        resp = self.setFunc('SetBinaryState', 'BinaryState', 0)
        self.state = resp

    def toggle(self):
        self.state = self.checkState()
        if self.state == 0:
            self.enable()
        else:
            self.disable()

    def postmaster(self, url, hd, data, tagname):
        try:
            rsp = post(url, headers=hd, data=data)
            if rsp.status_code != 200:
                print(rsp.reason)
                return None
            else:
                if hasattr(rsp, 'text'):
                    return self.tagger(rsp.text, tagname)
                else:
                    return "OK"
        except OSError as oe:
            print("WeMo unreachable!")
            print(str(oe))
            self.port = 0
            return None

    def getFunc(self, fname, tagname, url=None):
        hd = self.xmlHeads(fname)
        # tagname actually isn't passed in to the XML constructor
        data = self.xmlData(fname, tagname)

        # Be very clear for now
        if url is None:
            url = self.url
        else:
            url = url

        retval = self.postmaster(url, hd, data, tagname)

        return retval

    def setFunc(self, fname, tagname, value, url=None):
        hd = self.xmlHeads(fname)
        # tagname *is* passed in to the XML constructor
        data = self.xmlData(fname, tagname, val=value)

        # Be very clear for now
        if url is None:
            url = self.url
        else:
            url = url

        retval = self.postmaster(url, hd, data, tagname)

        return retval

    def xmlHeads(self, soapa):
        SOAPurn = '"urn:Belkin:service:basicevent:1#%s"' % (soapa)

        return {'Content-Type': 'text/xml', 'SOAPACTION': SOAPurn}

    def xmlData(self, tag, tname, val=''):
        data1 = ''
        data1 += "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
        data1 += "<s:Envelope xmlns:s="
        data1 += "\"http://schemas.xmlsoap.org/soap/envelope/\""
        data1 += "s:encodingStyle="
        data1 += "\"http://schemas.xmlsoap.org/soap/encoding/\">"
        data1 += "<s:Body><u:%s xmlns:u=" % (tag)
        data1 += "\"urn:Belkin:service:basicevent:1\">"
        data1 += "<%s>%s</%s>" % (tname, val, tname)
        data1 += "</u:%s></s:Body></s:Envelope>" % (tag)

        return data1

    def tagger(self, txt, tag):
        tagBStr = '<%s>' % (tag)
        tagEStr = '</%s>' % (tag)
        ln = len(tagBStr)
        beg = txt.index(tagBStr)
        end = txt.index(tagEStr)

        try:
            rstr = txt[beg+ln:end]
        except ValueError as ve:
            # Implies that the substring wasn't/couldn't be found
            rstr = None

        return rstr

    def portSearch(self, led=None):
        port = 0

        # Record the time (ticks in ms since boot if NTP isn't set up/called)
        self.checkTime = time.ticks_ms()

        # If there's a port already specified, skip all the blinky stuff
        #   to cut down on nighttime blinks
        if self.port != 0:
            # If we have a port, just try that one and see if it responds.
            #   If it does not, *then* do the full search
            answer = self.getFunc('GetSignalStrength', 'SignalStrength')
            if answer is not None:
                print("Port %d still worked :)" % (self.port))
                return self.port

        for testport in range(49152, 49156):
            tstr = 'http://%s:%s%s' % (self.ip, testport, self.service)
            #
            # http://192.168.1.169:49153/upnp/control/basicevent1
            #
            # Default function that all/most WeMo devices should support
            #  Could use FriendlyName too I suppose
            try:
                print("Attempting to contact %s" % (tstr))
                if led is not None:
                    utils.blinken(led, 0.25, 2)
                    led.on()

                answer = self.getFunc('GetSignalStrength', 'SignalStrength',
                                      url=tstr)

                if answer is not None:
                    print("Port %d worked :)" % (testport))
                    port = testport

                    self.port = port

                    # Update the URL to the correct one
                    self.full = "%s:%s" % (self.ip, port)
                    self.url = "http://%s%s" % (self.full, self.service)

                    if led is not None:
                        led.off()

                    # Jump out of the loop early
                    break
                time.sleep(0.25)
            except OSError as oe:
                # This was a bad port so move along
                print("Port %d failed :(" % (testport))
                print(str(oe))
            finally:
                if led is not None:
                    led.off()
            print("Pausing for 0.25 seconds before next query")

        return port
