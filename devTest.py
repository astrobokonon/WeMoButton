import wemo
import time

wemoip = '192.168.1.169'

print("Making WeMo object ...")
wemoObj = wemo.switch(wemoip)
print("Initial state:")
print("%s state: %s" % (wemoObj.name, wemoObj.state))
time.sleep(2.5)

wemoObj.toggle()
print("%s state: %s" % (wemoObj.name, wemoObj.state))

time.sleep(5)

wemoObj.toggle()
print("%s state: %s" % (wemoObj.name, wemoObj.state))

print()
