#!/usr/bin/python3

import time
import logging as L

class NeatoCommandInterface(object):
    "Neato Command Interface abstraction interface"
    def open(self):
        pass
    def close(self):
        pass
    def ready(self):
        return False
    def flush(self):
        pass
    def put(self, line="Help"):
        return ""
    def get(self):
        return ""

class NCISimulator(NeatoCommandInterface):
    "Neato Command Interface for simulation"
    lastcmd=""
    def open(self):
        pass
    def close(self):
        pass
    def ready(self):
        return True
    def flush(self):
        pass
    def put(self, lines):
        self.lastcmd += lines.strip() + "\n"
    def get(self):
        import neatocmdsim as nsim
        requests = self.lastcmd.split('\n')
        self.lastcmd = ""
        response = ""
        for i in range(0,len(requests)):
            response += nsim.fake_respose(requests[i].strip())

        return response

import serial  # sudo apt-get install python3-serial
class NCISerial(NeatoCommandInterface):
    "Neato Command Interface for serial ports"

    def __init__(self, port="/dev/ttyACM0", baudrate=115200, timeout=0.5):
        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baudrate = baudrate
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.timeout = timeout
        #self.ser.xonxoff= False
        #self.ser.rtscts = False
        #self.ser.dsrdtr = False
        self.ser.write_timeout = 2
        self.isready = False

    def open(self):
        try:
            self.ser.open()
            self.isready = True
        except Exception as e:
            L.error("Error open serial port: " + str(e))
            self.isready = False

    def close(self):
        self.isready = False
        ser.close()

    def ready(self):
        if self.isready:
            return self.ser.isOpen()
        return False

    def flush(self):
        if self.ready():
            self.ser.flushInput()
            self.ser.flushOutput()
            self.ser.flush()

    def put(self, line):
        if self.ready() == False:
            return ""
        sendcmd = line.strip() + "\n"
        self.ser.write(sendcmd.encode('ASCII'))
        self.ser.flush()

    def get(self):
        if self.ready() == False:
            return ""
        retval = ""
        while True:
            try:
                L.debug('readline ...')
                response = self.ser.readline()
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
            retval += response + "\n"
        return retval

import socket
class NCINetwork(NeatoCommandInterface):
    "Neato Command Interface for TCP pipe"
    def __init__(self, address="localhost", port=3333, timeout=1):
        self.address = address
        self.port = port
        self.timeout = timeout

    def open(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.address, self.port))
        L.debug ('Client has been assigned socket name' + str(self.sock.getsockname()))
        self.sock.setblocking(True)
        self.sock.settimeout(self.timeout)
        self.data = ""

    def close(self):
        self.sock.close()

    def ready(self):
        #return False
        #time.sleep(1)
        return True

    def flush(self):
        pass

    def put(self, line):
        sendcmd = line.strip() + "\n"
        L.debug ('cli snd: ' + sendcmd)
        self.sock.sendall (bytes(sendcmd, 'ascii'))
        return ""

    def get(self):
        BUFFER_SIZE = 4096
        MAXIUM_SIZE = BUFFER_SIZE * 5

        cli_log_head = "CLI2SVR" + str(self.sock.getpeername())
        response=""
        while 1:
            try:
                recvdat = self.sock.recv(BUFFER_SIZE)
            except socket.timeout:
                L.debug('timeout read')
                break
            if not recvdat:
                # EOF, client closed, just return
                L.info(cli_log_head + " disconnected: " + str(self.sock.getpeername()))
                return
            L.debug(cli_log_head + "recv  size=" + str(len(recvdat)))
            self.data += str(recvdat, 'ascii')
            cntdata = self.data.count('\n')
            L.debug(cli_log_head + " the # of newline: %d"%cntdata)
            if (cntdata < 1):
                L.debug(cli_log_head + " not receive newline, skip: " + self.data)
                continue
            requests = self.data.split('\n')
            response += '\n'.join(requests[0:-1]) + "\n"
            self.data = requests[-1]
            L.debug('split and merge: ' + '\n'.join(requests[0:-2]) + "\n" + requests[-1])
        L.debug("get() return: " + response + self.data + "\n")
        return response + self.data + "\n"

