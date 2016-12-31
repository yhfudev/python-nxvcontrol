#!/usr/bin/python3

import time
import logging as L
#L.basicConfig(filename='neatocmdapi.log', level=L.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

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
        cmdstr = self.lastcmd.strip() + "\n"
        self.lastcmd = ""
        requests = cmdstr.split('\n')
        response = ""
        for i in range(0,len(requests)):
            retline = nsim.fake_respose(requests[i].strip())
            retline.strip() + "\n"
            retline = retline.replace('\x1A', '\n')
            retline = retline.replace('\r\n', '\n')
            retline = retline.replace('\n\n', '\n')
            response += retline

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
            L.error("[NCISerial] Error open serial port: " + str(e))
            self.isready = False
            return False
        return True

    def close(self):
        self.isready = False
        self.ser.close()

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

    def get(self):
        if self.ready() == False:
            return ""
        retval = ""
        while True:
            try:
                #L.debug('[NCISerial] readline ...')
                response = self.ser.readline()
            except TimeoutError:
                L.debug('[NCISerial] timeout read')
                break
            if len(response) < 1:
                L.debug('[NCISerial] read null')
                break
            response = response.decode('ASCII').strip()
            #L.debug('[NCISerial] received: ' + response)
            #L.debug('read size=' + len(response) )
            if len(response) < 1:
                L.debug('[NCISerial] read null 2')
                break
            if len(response) == 1:
                if response[0] == '\x1A':
                    break
            response = response.replace('\x1A', '\n')
            response = response.replace('\r\n', '\n')
            #response = response.replace('\n\n', '\n')
            retval += response + "\n"
        retval = retval.replace('\n\n', '\n')
        return retval.strip() + "\n\n"

import socket
class NCINetwork(NeatoCommandInterface):
    "Neato Command Interface for TCP pipe"
    def __init__(self, address="localhost", port=3333, timeout=2):
        self.address = address
        self.port = port
        self.timeout = timeout
        self.isready = False

    def open(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(15)
        try:
            self.sock.connect((self.address, self.port))
            self.isready = True
        except socket.timeout:
            self.sock = None
            self.isready = False
            return False;
        self.sock.settimeout(None)
        L.debug ('[NCINetwork] Client has been assigned socket name' + str(self.sock.getsockname()))
        self.sock.setblocking(True)
        self.sock.settimeout(self.timeout)
        self.data = ""
        return True

    def close(self):
        self.isready = False
        self.sock.close()

    def ready(self):
        return self.isready

    def flush(self):
        #self.sock.flush()
        pass

    def put(self, line):
        sendcmd = line.strip() + "\n"
        L.debug ('[NCINetwork] cli snd: ' + sendcmd)
        self.sock.sendall (bytes(sendcmd, 'ascii'))
        #self.sock.flush()
        return ""

    def get(self):
        BUFFER_SIZE = 4096
        #MAXIUM_SIZE = BUFFER_SIZE * 5

        cli_log_head = "[NCINetwork] " + str(self.sock.getpeername())
        while True:
            try:
                recvdat = self.sock.recv(BUFFER_SIZE)
            except socket.timeout:
                L.debug(cli_log_head + 'timeout read')
                if len(self.data) > 0:
                    break
                continue
            except os.ConnectionResetError:
                L.debug(cli_log_head + 'peer reset')
                break
            if not recvdat:
                # EOF, client closed, just return
                L.info(cli_log_head + " disconnected: " + str(self.sock.getpeername()))
                self.data += "\n\n"
            else:
                #L.debug(cli_log_head + "recv  size=" + str(len(recvdat)))
                recvstr = str(recvdat, 'ascii')
                recvstr = recvstr.replace('\x1A', '\n')
                recvstr = recvstr.replace('\r\n', '\n')
                self.data += recvstr

            # TODO: clean the lines, remove blanks for each line from the begin and end
            # ...
            if self.data.find("\n\n") >= 0:
                break

        pos = self.data.find("\n\n")
        if pos < 0:
            retstr = self.data
            self.data = ""
            return retstr.strip() + "\n\n"
        else:
            # end mode:
            self.data = self.data.lstrip()
            pos = self.data.find("\n\n")
            if pos < 0:
                # this means the "\n\n" is at left(and be removed)
                L.debug(cli_log_head + 'tcp return null')
                return "\n\n"
            else:
                retstr = self.data[0:pos]
                self.data = self.data[pos+2:len(self.data)]
                L.debug(cli_log_head + 'tcp return ' + retstr)
                return retstr + "\n\n"


from multiprocessing import Queue, Lock
import threading
import heapq
from datetime import datetime
from itertools import count

class MyHeap(object):
    def __init__(self, initial=None, key=lambda x:x):
        self._counter = count()
        self.key = key
        if initial:
            self._data = [(key(item), next(self._counter), item) for item in initial]
            heapq.heapify(self._data)
        else:
            self._data = []

    def size(self):
        return len(self._data)

    def push(self, item):
        heapq.heappush(self._data, (self.key(item), next(self._counter), item))

    def pop(self):
        return heapq.heappop(self._data)[-1]

# MailPipe
#   each pipe has its address
#   the message in the pipe is in Queue
class MailPipe(object):
    def __init__(self):
        self._counter = count()
        self._idx = {}

    # declair a new mail pipe, return the handler
    def declair(self):
        mid = next(self._counter)
        self._idx[mid] = Queue()
        return mid

    # close a mail pipe; mid the id of the mail pipe
    def close(self, mid):
        self._idx.pop(mid)
        pass

    # get the # of mail pipe
    def size(self, mid):
        return len(self._idx)

    # get the # of messages of a specified mail pipe
    def count(self, mid):
        if mid in self._idx:
            return self._idx[mid].qsize()
        return -1

    # get a message from specified mail pipe
    def get(self, mid, isblock=True):
        if mid in self._idx:
            return self._idx[mid].get(isblock)
        return None

    # add a message to a specified mail pipe
    def put(self, mid, msg, isblock=True):
        if mid in self._idx:
            self._idx[mid].put(msg, isblock)
            return True
        return False

# internal class
class AtomTask(object):
    PRIORITY_DEFAULT = 5
    PRIORITY_MAX=255

    def __init__(self, req=None, newid=0, priority=None):
        self.req = req # user define
        self.tid = newid
        self.priority = priority
        self.execute_time = None
        self.request_time = None
        self.start_time = None
        self.finish_time = None
        self.is_run = False

    def setPriority(self, pri):
        self.priority = pri

    def setRequestTime(self, etime):
        self.request_time = etime

    def setExecuteTime(self, etime):
        self.execute_time = etime

    def setStartTime(self, etime):
        self.start_time = etime

    def setFinishTime(self, etime):
        self.finish_time = etime

# each task will executed until finished
# supports priority, 0 -- critial for important task, 1-n -- normal priority tasks
# supports execute at a exact time.
class AtomTaskScheduler(object):

    # use two queues to accept and cache the requests,
    #    queue_priority is for tasks with priority
    #    queue_time is for tasks with exact time
    # use two internal heap/priorityQueue to manage the task to decide which task should run next
    #    heap_priority sort and store the task will be run
    #    heap_time sort and store the tasks of time bound
    # and a main function/loop to move the requests from queue_xxx to heap_xxx, and run the task from heap_priority
    #
    # loop:
    #  move tasks from queue_priority to heap_priority
    #  move tasks from queue_time to heap_time
    #  if heap_time has expired tasks need to execute, move the tasks(priority=1) to heap_priority
    #  if heap_priority has task, do the task, remove it from heap_priority, return results(id, request time, begin time, finish time, response)
    #  if has do task, goto loop
    #  wait_time=1
    #  if has task in heap_time, wait_time = wait time for the top task
    #  cond_wait(wait_time)
    def __init__(self, cb_task=None):
        self.cb_task = cb_task
        self.queue_priority = Queue()
        self.queue_time = Queue()
        self.heap_priority = MyHeap(key=lambda x:x.priority);
        self.heap_time = MyHeap(key=lambda x:x.execute_time);

        self._counter = count()
        self.idlock = Lock()
        self.apilock = Lock()
        self.apicond = threading.Condition(self.apilock)

    # create a new request id
    def getNewId(self):
        self.idlock.acquire()
        try:
            return next(self._counter)
        finally:
            self.idlock.release()

    # request for a task, with the priority
    def request(self, req, priority):
        newid = self.getNewId()
        newreq = AtomTask(req=req, newid=newid, priority=priority)
        newreq.setRequestTime(datetime.now())
        self.queue_priority.put(newreq)
        with self.apicond:
            self.apicond.notifyAll()
        return newid

    # request for a task, with the exact time
    def request_time (self, req, exacttime):
        newid = self.getNewId()
        newreq = AtomTask(req=req, newid=newid)
        newreq.setRequestTime(datetime.now())
        newreq.setExecuteTime(exacttime)
        self.queue_time.put(newreq)
        with self.apicond:
            self.apicond.notifyAll()
        return newid

    def do_work_once (self):
        # move tasks from queue_priority to heap_priority
        while self.queue_priority.qsize() > 0:
            newreq = None
            try:
                newreq = self.queue_priority.get()
                L.debug("get req from queue_priority: " + str(newreq))
            except Queue.Empty:
                break;
            self.heap_priority.push (newreq)
        # move tasks from queue_time to heap_time
        while self.queue_time.qsize() > 0:
            newreq = None
            try:
                newreq = self.queue_time.get()
            except Queue.Empty:
                break;
            self.heap_time.push (newreq)
        # if heap_time has expired tasks need to execute, move the tasks(priority=1) to heap_priority
        wait_time=0.5 # seconds, wait time for cond
        while (self.heap_time.size() > 0):
            newreq = self.heap_time.pop()
            tmnow = datetime.now()
            if newreq.execute_time <= tmnow:
                newreq.setPriority(1)
                self.heap_priority.push(newreq)
            else:
                # push back the item
                delta = newreq.execute_time - tmnow
                wait_time = delta.days * 86400 + delta.seconds + delta.microseconds/1000000
                self.heap_time.push(newreq)
        # if heap_priority has task, do the task, remove it from heap_priority, return results(id, request time, begin time, finish time, response)
        if (self.heap_priority.size() > 0):
            newreq = self.heap_priority.pop()
            newreq.setStartTime(datetime.now())
            self.cb_task (newreq.tid, newreq.req)    # do the job
            newreq.setFinishTime(datetime.now())
            #return True # if has done task, goto loop
        if (self.heap_priority.size() > 0):
            wait_time = 0

        return wait_time

    def do_wait_queue(self, wait_time):
        # if has task in heap_time, wait_time = wait time for the top task
        try:
            #L.debug("waiting queues for " + str(wait_time) + " seconds ...")
            with self.apicond:
                self.apicond.wait(wait_time)
            #L.debug("endof wait!")
        except RuntimeError:
            #L.debug("wait timeout!")
            #time.sleep(0) # Effectively yield this thread.
            pass

    def stop(self):
        self.is_run = False

    def serve_forever (self):
        self.is_run = True
        while self.is_run:
            wait_time = self.do_work_once()
            if self.is_run and wait_time > 0:
                self.do_wait_queue(wait_time)

#from urlparse import urlparse
from urllib.parse import urlparse
import neatocmdapi

# the service thread,
# 
class NCIService(object):
    "Neato Command Interface all"

    def ready(self):
        return self.isready

    # target: example: tcp://localhost:3333 sim://
    def __init__(self, target="tcp://localhost:3333", timeout=2):
        "target accepts: 'tcp://localhost:3333', 'dev://ttyUSB0:115200', 'dev://COM12:115200', 'sim:' "
        self.api = None
        self.th_sche = None
        self.sche = None
        self.isready = False
        self.mailbox = MailPipe()

        result = urlparse(target)
        if result.scheme == "tcp":
            addr = result.netloc.split(':')
            port = 3333
            if len(addr) > 1:
                port = int(addr[1])
            self.api = neatocmdapi.NCINetwork(timeout = timeout, port = port, address=addr[0])

        elif result.scheme == "sim":
            self.api = neatocmdapi.NCISimulator()

        else:
            addr = result.netloc.split(':')
            baudrate = 115200
            if len(addr) > 1:
                baudrate = int(addr[1])
            port = addr[0]
            import re
            if re.match('tty.*', port):
                port = "/dev/" + addr[0]
            L.debug('serial open: ' + port + ", " + str(baudrate))
            self.api = neatocmdapi.NCISerial(timeout = timeout, port = port, baudrate = baudrate)

    # block read and get
    def get_request_block(self, req):
        self.api.put(req)
        return self.api.get()

    #def cb_task1(self, tid, req):
    #    L.debug("do task: tid=" + str(tid) + ", req=" + str(req))
    #    resp = self.get_request_block(req)

    def open(self, cb_task1):
        try:
            L.debug('api.open() ...')
            self.api.open()
            time.sleep(0.5)
            cnt=1
            while self.api.ready() == False and cnt < 2:
                time.sleep(1)
                cnt += 1
            if self.api.ready() == False:
                self.api = None
                return False
            self.api.flush()

            # creat a thread to run the task in background
            self.sche = AtomTaskScheduler(cb_task=cb_task1)

            self.th_sche = threading.Thread(target=self.sche.serve_forever)
            self.th_sche.setDaemon(True)
            self.th_sche.start()

        except Exception as e1:
            L.error ('Error in read serial: ' + str(e1))
            return False

        self.isready = True
        return True

    def close(self):
        isrun = False;
        if self.th_sche != None:
            if self.th_sche.isAlive():
                if self.sche != None:
                    self.sche.stop()
                isrun = True
        if isrun:
            while self.th_sche.isAlive():
                time.sleep(1)
        self.api.close()
        self.api = None
        self.sche = None
        self.th_sche = None
        self.isready = False

    def request(self, req):
        if self.ready() and self.sche != None:
            return self.sche.request(req, 5)
        return -1

    def request_time (self, req, exacttime):
        if self.ready() and self.sche != None:
            return self.sche.request_time(req, exacttime)
        return -1


def test_nci_service():
    a = NCIService()



def test_heap_priority():
    hp = MyHeap()
    hp.push (5)
    hp.push (3)
    hp.push (2)
    hp.push (0)
    hp.push (6)
    hp.push (4)
    hp.push (1)
    tmpre = hp.pop()
    while hp.size() > 0:
        tm = hp.pop()
        assert (tm > tmpre);
        tmpre = tm

def test_heap_time():
    hp = MyHeap()
    tm = datetime.now()
    hp.push(tm)
    time.sleep(0.01)
    tm = datetime.now()
    hp.push(tm)
    time.sleep(0.31)
    tm = datetime.now()
    hp.push(tm)
    tmpre = hp.pop()
    while hp.size() > 0:
        tm = hp.pop()
        assert (tm > tmpre);
        tmpre = tm

def test_heap_atomtask_priority():
    hp = MyHeap(key=lambda x:x.priority);
    newreq = AtomTask(req="req4", priority=4)
    hp.push (newreq)
    newreq = AtomTask(req="req2", priority=2)
    hp.push (newreq)
    newreq = AtomTask(req="req1", priority=1)
    hp.push (newreq)
    newreq = AtomTask(req="req0", priority=0)
    hp.push (newreq)
    newreq = AtomTask(req="req5", priority=5)
    hp.push (newreq)
    newreq = AtomTask(req="req3", priority=3)
    hp.push (newreq)
    tmpre = hp.pop()
    while hp.size() > 0:
        tm = hp.pop()
        assert (tm.priority > tmpre.priority);
        tmpre = tm

def test_heap_atomtask_time():
    hp = MyHeap(key=lambda x:x.execute_time);
    newreq = AtomTask(req="req1")
    newreq.setExecuteTime(datetime.now())
    hp.push(newreq)
    time.sleep(0.01)
    newreq = AtomTask(req="req2")
    newreq.setExecuteTime(datetime.now())
    hp.push(newreq)
    time.sleep(0.31)
    tm = datetime.now()
    newreq = AtomTask(req="req3")
    newreq.setExecuteTime(datetime.now())
    hp.push(newreq)

    tmpre = hp.pop()
    while hp.size() > 0:
        tm = hp.pop()
        assert (tm.execute_time > tmpre.execute_time);
        tmpre = tm


def test_heap_atomtask_priority_class():
    class TestContainer(object):
        def __init__(self):
            self.hp = MyHeap(key=lambda x:x.priority);
        def selftest(self):
            newreq = AtomTask(req="req4", priority=4)
            self.hp.push (newreq)
            newreq = AtomTask(req="req2", priority=2)
            self.hp.push (newreq)
            newreq = AtomTask(req="req1", priority=1)
            self.hp.push (newreq)
            newreq = AtomTask(req="req0", priority=0)
            self.hp.push (newreq)
            newreq = AtomTask(req="req5", priority=5)
            self.hp.push (newreq)
            newreq = AtomTask(req="req3", priority=3)
            self.hp.push (newreq)
            tmpre = self.hp.pop()
            while self.hp.size() > 0:
                tm = self.hp.pop()
                assert (tm.priority >= tmpre.priority);
                assert (tm.priority >= tmpre.priority);
                tmpre = tm
    tc = TestContainer()
    tc.selftest()

# test the AtomTaskScheduler in a function
def test_atomtask():
    def cb_task1(tid, req):
        L.debug("(infunc) do task: tid=" + str(tid) + ", req=" + str(req))
    #def cb_signal1(tid, request_time, start_time, finish_time, resp):
    #    L.debug("(infunc) signal: tid=" + str(tid) + ", reqtime=" + str(request_time) + ", starttime=" + str(start_time) + ", fintime=" + str(finish_time) + ", resp=" + str(resp) )

    def th_setup(sche):
        sche.request("init work 2-1", 2)
        sche.request("init work 2-3", 2)
        sche.request("init work 1-2", 1)
        sche.request("init work 2-2", 2)
        sche.request("init work 0-1", 0)
        sche.request("init work 1-1", 1)
        sche.request("init work 2-4", 2)
        sche.request("init work 0-2", 0)
        time.sleep(5)
        sche.request("normal work 5-1", 5)
        sche.request("normal work 5-2", 5)
        sche.request("normal work 5-3", 5)
        sche.request("normal work 5-4", 5)
        L.debug("sleep 5")
        time.sleep(5.31)
        L.debug("sche stop")
        sche.stop()

    sche = AtomTaskScheduler(cb_task=cb_task1)

    if 1 == 1:
        runT = threading.Thread(target=sche.serve_forever)
        runT.setDaemon(True)
        runT.start()
        th_setup(sche)
    else:
        runT = threading.Thread(target=th_setup, args=(sche,))
        runT.setDaemon(True)
        runT.start()
        sche.serve_forever()

# test the AtomTaskScheduler in a class
class TestAtomtask(object):
    def cb_task1(self, tid, req):
        L.debug("(inclas) do task: tid=" + str(tid) + ", req=" + str(req))
    #def cb_signal1(self, tid, request_time, start_time, finish_time, resp):
    #    L.debug("(inclas) signal: tid=" + str(tid) + ", reqtime=" + str(request_time) + ", starttime=" + str(start_time) + ", fintime=" + str(finish_time) + ", resp=" + str(resp) )

    def th_setup(self, sche):
        sche.request("init work 2-1", 2)
        sche.request("init work 2-3", 2)
        sche.request("init work 1-2", 1)
        sche.request("init work 2-2", 2)
        sche.request("init work 0-1", 0)
        sche.request("init work 1-1", 1)
        sche.request("init work 2-4", 2)
        sche.request("init work 0-2", 0)
        time.sleep(5)
        sche.request("normal work 5-1", 5)
        sche.request("normal work 5-2", 5)
        sche.request("normal work 5-3", 5)
        sche.request("normal work 5-4", 5)
        L.debug("sleep 5")
        time.sleep(5.31)
        L.debug("sche stop")
        sche.stop()

    def run_test(self):
        self.sche = AtomTaskScheduler(cb_task=self.cb_task1)

        if 1 == 0:
            runT = threading.Thread(target=self.sche.serve_forever)
            runT.setDaemon(True)
            runT.start()
            self.th_setup(self.sche)
        else:
            runT = threading.Thread(target=self.th_setup, args=(self.sche,))
            runT.setDaemon(True)
            runT.start()
            self.sche.serve_forever()
def test_atomtask_class():
    run1 = TestAtomtask()
    run1.run_test()

def testme():
    #test_heap_time()
    #test_heap_priority()
    #test_heap_atomtask_priority()
    #test_heap_atomtask_time()
    #test_heap_atomtask_priority_class()
    #test_atomtask()
    test_atomtask_class()
    #test_nci_service()


if __name__ == "__main__":
    testme()



