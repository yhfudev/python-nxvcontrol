#!/usr/bin/python3

import sys
import time
import argparse # argparse > optparse > getopt
import logging as L
from datetime import datetime

from multiprocessing import Queue, Lock

import neatocmdapi

L.basicConfig(level=L.DEBUG, format='%(levelname)s:%(message)s')

parser=argparse.ArgumentParser(description='Log battery data from USB port(serial) of a Neato Xv robot.')
#parser.add_argument('intergers', metavar='N', type=int, nargs='+', help='an integer for the accumulator')
parser.add_argument('-l', '--logfile', type=str, dest='fnlog', default="/dev/stderr", help='the file to output the log')
parser.add_argument('-o', '--output', type=str, dest='fnout', default="/dev/stdout", help='the file to output the data')
parser.add_argument('-a', '--target', type=str, dest='target', default="", help='tcp://localhost:3333, dev://ttyUSB0:115200, dev://COM12:115200, sim:')
parser.add_argument('-i', '--interval', type=float, dest='interval', default=0.5, help='the interval between log records')
parser.add_argument('-t', '--time', type=int, dest='time', default=0, help='the second time length of log records')
parser.add_argument('-d', '--drain', type=int, dest='draintime', default=0, help='the second time length of draining the battery(start fan motor)')
args = parser.parse_args()

if args.fnout == "/dev/stdout":
    L.info ("output data to standard output")
else:
    sys.stdout = open(args.fnout, 'w')

if args.fnlog == "/dev/stderr":
    L.info ("output log to standard error")
else:
    L.info ("output log to " + args.fnlog)
    ch = L.FileHandler(args.fnlog)
    ch.setLevel(L.DEBUG)
    ch.setFormatter(L.Formatter('%(asctime)s %(levelname)s:%(message)s'))
    L.getLogger().addHandler(ch)

serv = None
L.debug('serv.open() ...')
serv = neatocmdapi.NCIService(target=args.target.strip(), timeout=args.interval)

def cb_task(tid, req):
    L.debug("do task: tid=" + str(tid) + ", req=" + str(req))
    reqstr = req[0]
    resp = serv.get_request_block(reqstr)
    if resp != None:
        if resp.strip() != "":
            serv.mailbox.put(req[1], resp.strip())

mbox_id = serv.mailbox.declair()

if serv.open(cb_task) == False:
    L.error ('time out for connection')
    exit(0)

try:
    if args.draintime > 0:
        serv.request(["TestMode On\nSetMotor VacuumOn", mbox_id])
        time.sleep(args.draintime)
        serv.request(["SetMotor VacuumOff\nTestMode Off", mbox_id])

    list_commands = (
        'GetCharger',
        'GetAnalogSensors',
        )
    list_keys = (
        # GetAnalogSensors:
        'CurrentInmA',
        'BatteryVoltageInmV',
        'BatteryTemp0InC',
        'BatteryTemp1InC',
        'ChargeVoltInmV',
        # GetCharger:
        'VBattV',
        'VExtV',
        'FuelPercent',
        'ChargingActive',
        'Charger_mAH',
        # others:
        'UIButtonInmV',
        'VacuumCurrentInmA',
        'SideBrushCurrentInmA',
        'VoltageReferenceInmV',
        'BattTempCAvg[0]',
        'BattTempCAvg[1]',
        'BatteryOverTemp',
        'ChargingEnabled',
        'ConfidentOnFuel',
        'OnReservedFuel',
        'EmptyFuel',
        'BatteryFailure',
        'ExtPwrPresent',
        'ThermistorPresent[0]',
        'ThermistorPresent[1]',
        #
        #'WallSensorInMM',
        #'LeftDropInMM',
        #'RightDropInMM',
        #'LeftMagSensor',
        #'RightMagSensor',
        #'AccelXInmG',
        #'AccelYInmG',
        #'AccelZInmG',
        )
    tm_begin = datetime.now()
    print ("# start time " + str(tm_begin) + ", " + ", ".join(list_keys))
    while True:
        tm_now = datetime.now()
        delta = tm_now - tm_begin
        if args.time > 0:
            if delta.total_seconds() > args.time:
                L.debug("exceed time!")
                break

        data = dict()
        sendcmd = ""
        for cmd0 in list_commands:
            L.debug ('send command ' + cmd0)
            sendcmd += cmd0 + "\n"
        serv.request([sendcmd, mbox_id])

        tm_now = datetime.now()
        #record = [-1] * 16
        respstr = serv.mailbox.get(mbox_id)
        retlines = respstr.strip() + '\n'
        responses = retlines.split('\n')
        for i in range(0,len(responses)):
            response = responses[i].strip()
            L.debug('received: ' + response)
            #L.debug('read size=' + len(response) )
            if len(response) < 1:
                L.debug('read null 2')
                break
            lst = response.split(',')
            #L.debug('lst=' + ",".join(lst))
            #L.debug('lst size=%d'%lst.__len__())
            #L.debug('lst len=%d'%len(lst))
            if len(lst) > 1:
                if lst[0].lower() == 'Label'.lower():
                    # ignore
                    L.debug('ignore header')
                elif lst[0] in list_keys:
                    data[lst[0]] = lst[1]
                    L.debug("process response: " + response)
                else:
                    L.debug("ignore return response: " + response)
            else:
                L.debug('ignore response with: ' + lst[0])

        #fmt0="%d.%06d" + ", " + ", ".join(data[x] for x in list_keys)
        linedata = ""
        for val in list_keys:
            if val in data:
                linedata += data[val]
            linedata += ", "
        fmt0="%d.%06d" + ", " + linedata

        L.debug("fmt=" + fmt0)
        print (fmt0 %(delta.days * 86400 + delta.seconds, delta.microseconds)) # (24*60*60)=86400
        sys.stdout.flush()

        tm_now2 = datetime.now()
        delta = tm_now2 - tm_now
        timepast = 1.0 * delta.microseconds / 1000000
        timepast += delta.days * 86400 + delta.seconds
        if timepast < args.interval:
            time.sleep(args.interval - timepast)

    serv.close()

except Exception as e1:
    L.error ('Error in read serial: ' + str(e1))
