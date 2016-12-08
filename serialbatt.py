#!/usr/bin/python3

import sys
import time
import argparse # argparse > optparse > getopt
import logging as L
from datetime import datetime
import serial  # sudo apt-get install python3-serial

#L.basicConfig(filename='logserial.txt', level=L.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')
ch = L.StreamHandler(sys.stderr)
ch.setLevel(L.DEBUG) #(L.WARNING)
ch.setFormatter(L.Formatter('%(levelname)s:%(message)s'))
L.getLogger().addHandler(ch)

parser=argparse.ArgumentParser(description='Log battery data from USB port(serial) of a Neato Xv robot.')
#parser.add_argument('intergers', metavar='N', type=int, nargs='+', help='an integer for the accumulator')
parser.add_argument('-l', '--logfile', type=str, dest='fnlog', default="/dev/stderr", help='the file to output the log')
parser.add_argument('-o', '--output', type=str, dest='fnout', default="/dev/stdout", help='the file to output the data')
parser.add_argument('-b', '--baudrate', type=int, dest='baudrate', default=115200, help='the baudrate of serial port')
parser.add_argument('-p', '--port', type=str, dest='port', default="/dev/ttyACM0", help='the path to serial port')
parser.add_argument('-i', '--interval', type=int, dest='interval', default=0.5, help='the interval between log records')
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
    L.basicConfig(filename=args.fnlog, level=L.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')

ser=serial.Serial()
ser.port = args.port
ser.baudrate = args.baudrate
ser.bytesize = serial.EIGHTBITS
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE
ser.timeout = args.interval
#ser.xonxoff= False
#ser.rtscts = False
#ser.dsrdtr = False
ser.write_timeout = 2

#debug
if 0 == 1:
    tm_begin = datetime.now()
    time.sleep(3)
    tm_now = datetime.now()
    delta = tm_now - tm_begin
    print ("second=" + str(delta.seconds))
    print ("milli second=%d.%06d"%(delta.seconds, delta.microseconds))
    print ("delta: " + str(delta))
    exit()


try:
    ser.open()
except Exception as e:
    L.error("Error open serial port: " + str(e))
    exit()

if ser.isOpen():
    try:
        ser.flushInput()
        ser.flushOutput()

        # clean the input/output
        ser.write("Help\n".encode('ASCII'))
        ser.flush()
        while True:
            response = ser.readline()
            if len(response) < 1:
                L.debug('read null')
                break
            response = response.decode('ASCII').strip()
            if len(response) < 1:
                break

        if args.draintime > 0:
            ser.write("TestMode On\n".encode('ASCII'))
            ser.write("SetMotor VacuumOn\n".encode('ASCII'))
            ser.flush()
            time.sleep(args.draintime)
            ser.write("SetMotor VacuumOff\n".encode('ASCII'))
            ser.write("TestMode Off\n".encode('ASCII'))
            ser.flush()

        list_commands = (
            'GetCharger',
            'GetAnalogSensors',
            )
        list_keys = (
            # GetAnalogSensors
            'CurrentInmA',
            'BatteryVoltageInmV',
            'BatteryTemp0InC',
            'BatteryTemp1InC',
            'ChargeVoltInmV',
            # GetCharger
            'VBattV',
            'VExtV',
            'FuelPercent',
            'ChargingActive',
            'Charger_mAH',
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

            for cmd0 in list_commands:
                L.debug ('send command ' + cmd0)
                sendcmd = cmd0 + "\n"
                ser.write(sendcmd.encode('ASCII'))
            ser.flush()

            data = dict()
            tm_now = datetime.now()
            record = [-1] * 16
            while True:
                try:
                    L.debug('readline ...')
                    response = ser.readline()
                except TimeoutError:
                    L.debug('timeout read')
                    break
                if len(response) < 1:
                    L.debug('read null')
                    break
                response = response.decode('ASCII').strip()
                L.debug('received: ' + response)
                #L.debug('read size=' + len(response) )
                if len(response) < 1:
                    L.debug('read null 2')
                    break
                if len(response) == 1:
                    if response[0] == '\x1A':
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

        ser.close()

    except Exception as e1:
        L.error ('Error in read serial: ' + str(e1))

else:
    L.error('Cannot open serial port')


