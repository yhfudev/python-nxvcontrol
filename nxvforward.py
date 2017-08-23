#!/usr/bin/env python3
# encoding: utf8
#
# Copyright 2016-2017 Yunhui Fu <yhfudev@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# For further info, check https://github.com/yhfudev/python-nxvcontrol.git

try:
    import Tkinter as tk
    import ttk
    import ScrolledText
    import tkFileDialog as fd
    import Queue
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    from tkinter.scrolledtext import ScrolledText
    import tkinter.filedialog as fd
    import multiprocessing
    from multiprocessing import Queue

import os
import sys
import importlib.util as importutil
#if None != importlib.find_loader("intl"):
#if None != importutil.find_spec("intl"):

import time
from threading import Thread
import queue

import logging as L
L.basicConfig(filename='nxvforward.log', level=L.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
# if we use the textarea to output log. There's problem when multiple threads output to the same textarea
config_use_textarea_log=False

import neatocmdapi
import guilog

import locale
import gettext
_=gettext.gettext

def gettext_init():
    global _
    langs = []

    language = os.environ.get('LANG', None)
    if (language):
        langs += language.split(":")
    language = os.environ.get('LANGUAGE', None)
    if (language):
        langs += language.split(":")
    lc, encoding = locale.getdefaultlocale()
    if (lc):
        langs += [lc]
    # we know that we have
    langs += ["en_US", "zh_CN"]
    local_path = os.path.realpath(os.path.dirname(sys.argv[0]))
    local_path = "languages/"
    APP_NAME="nxvcontrol"
    gettext.bindtextdomain(APP_NAME, local_path)
    gettext.textdomain(APP_NAME)
    lang = gettext.translation(APP_NAME, local_path, languages=langs, fallback = True)
    #_=gettext.gettext
    _=lang.gettext
    L.debug("local=" + str(lc) + ", encoding=" + str(encoding) + ", langs=" + str(langs) + ", lang=" + str(lang) )

str_progname=_("nxvForward")
str_version="0.1"

LARGE_FONT= ("Verdana", 18)
NORM_FONT = ("Helvetica", 12)
SMALL_FONT = ("Helvetica", 8)

def set_readonly_text(text, msg):
    text.config(state=tk.NORMAL)
    text.delete(1.0, tk.END)
    text.insert(tk.END, msg)
    text.config(state=tk.DISABLED)

class MyTkAppFrame(ttk.Notebook):

    # the req is a list
    def cb_task(self, tid, req):
        L.debug("do task: tid=" + str(tid) + ", req=" + str(req))
        reqstr = req[0]
        resp = self.serv.get_request_block(reqstr)
        if resp != None:
            if resp.strip() != "":
                self.serv.mailbox.put(req[1], resp)

    def do_stop(self):
        isrun = False;
        if self.runth_svr != None:
            if self.runth_svr.isAlive():
                #L.info('signal server to stop ...')
                self.server.shutdown()
                #L.info('server close ...')
                self.server.server_close()
                #L.info('server closed.')
                isrun = True
        if isrun == False:
            L.info('server is not running. skip')
        if self.serv != None:
            self.serv.close()
            self.serv = None

        self.btn_svr_start.config(state=tk.NORMAL)
        self.btn_svr_stop.config(state=tk.DISABLED)

        #return

    def do_start(self):
        import socketserver as ss
        import neatocmdsim as nsim

        class ThreadedTCPRequestHandler(ss.BaseRequestHandler):
            # override base class handle method
            def handle(self):
                self.serv = self.server.serv
                BUFFER_SIZE = 4096
                MAXIUM_SIZE = BUFFER_SIZE * 5
                data = ""
                L.info("server connectd by client: " + str(self.client_address))
                mbox_id = self.serv.mailbox.declair()

                cli_log_head = "CLI" + str(self.client_address)
                while 1:
                    try:
                        # receive the requests
                        recvdat = self.request.recv(BUFFER_SIZE)
                        if not recvdat:
                            # EOF, client closed, just return
                            L.info(cli_log_head + " disconnected: " + str(self.client_address))
                            break
                        data += str(recvdat, 'ascii')
                        L.debug(cli_log_head + " all of data: " + data)
                        cntdata = data.count('\n')
                        L.debug(cli_log_head + " the # of newline: %d"%cntdata)
                        if (cntdata < 1):
                            L.debug(cli_log_head + " not receive newline, skip: " + data)
                            continue
                        # process the requests after a '\n'
                        requests = data.split('\n')
                        for i in range(0, cntdata):
                            # for each line:
                            request = requests[i].strip()
                            L.info(cli_log_head + " request [" + str(i+1) + "/" + str(cntdata) + "] '" + request + "'")
                            self.serv.request ([request, mbox_id])
                            response = self.serv.mailbox.get(mbox_id)
                            if response != "":
                                L.debug(cli_log_head + 'send data back: sz=' + str(len(response)))
                                self.request.sendall(bytes(response, 'ascii'))

                        data = requests[-1]

                    except BrokenPipeError:
                        L.error (cli_log_head + 'remote closed: ' + str(self.client_address))
                        break
                    except ConnectionResetError:
                        L.error (cli_log_head + 'remote reset: ' + str(self.client_address))
                        break
                    except Exception as e1:
                        L.error (cli_log_head + 'Error in read serial: ' + str(e1))
                        break

                L.error (cli_log_head + 'close: ' + str(self.client_address))
                self.serv.mailbox.close(mbox_id)

        class ThreadedTCPServer(ss.ThreadingMixIn, ss.TCPServer):
            daemon_threads = True
            allow_reuse_address = True
            # pass the serv to handler
            def __init__(self, host_port_tuple, streamhandler, serv):
                super().__init__(host_port_tuple, streamhandler)
                self.serv = serv

        if self.runth_svr != None:
            if self.runth_svr.isAlive():
                L.info('server is already running. skip')
                return True

        L.info('connect to ' + self.conn_port.get())
        self.serv = neatocmdapi.NCIService(target=self.conn_port.get().strip(), timeout=0.5)
        if self.serv.open(self.cb_task) == False:
            L.error ('Error in open serial')
            return False

        L.info('start server ' + self.bind_port.get())
        b = self.bind_port.get().split(":")
        L.info('b=' + str(b))
        HOST=b[0]
        PORT=3333
        if len(b) > 1:
            PORT=int(b[1])
        L.info('server is running ...')
        try:
            self.server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler, self.serv)
        except Exception as e:
            L.error("Error in starting service: " + str(e))
            return False
        ip, port = self.server.server_address
        L.info("server listened to: " + str(ip) + ":" + str(port))
        self.runth_svr = Thread(target=self.server.serve_forever)
        self.runth_svr.setDaemon(True) # When closing the main thread, which is our GUI, all daemons will automatically be stopped as well.
        self.runth_svr.start()

        self.btn_svr_start.config(state=tk.DISABLED)
        self.btn_svr_stop.config(state=tk.NORMAL)
        L.info('server started.')
        return True

    def get_log_text(self):
        return self.text_log

    def __init__(self, tk_frame_parent):
        global config_use_textarea_log
        ttk.Notebook.__init__(self, tk_frame_parent)
        nb = self
        self.runth_svr = None
        self.serv = None
        self.serv_cli = None

        guilog.rClickbinder(tk_frame_parent)

        # page for About
        page_about = ttk.Frame(nb)
        lbl_about_head = tk.Label(page_about, text=_("About"), font=LARGE_FONT)
        lbl_about_head.pack(side="top", fill="x", pady=10)
        lbl_about_main = tk.Label(page_about
                , font=NORM_FONT
                , text="\n" + str_progname + "\n" + str_version + "\n"
                    + _("Forward Neato XV control over network") + "\n"
                    + "\n"
                    + _("Copyright © 2015–2016 The nxvForward Authors") + "\n"
                    + "\n"
                    + _("This program comes with absolutely no warranty.") + "\n"
                    + _("See the GNU General Public License, version 3 or later for details.")
                )
        lbl_about_main.pack(side="top", fill="x", pady=10)

        # page for server
        page_server = ttk.Frame(nb)
        lbl_svr_head = tk.Label(page_server, text=_("Server"), font=LARGE_FONT)
        lbl_svr_head.pack(side="top", fill="x", pady=10)

        frame_svr = ttk.LabelFrame(page_server, text=_("Setup"))

        line=0
        bind_port_history = ('localhost:3333', '127.0.0.1:4444', '0.0.0.0:3333')
        self.bind_port = tk.StringVar()
        lbl_svr_port = tk.Label(frame_svr, text=_("Bind Address:"))
        lbl_svr_port.grid(row=line, column=0, padx=5, sticky=tk.N+tk.S+tk.W)
        combobox_bind_port = ttk.Combobox(frame_svr, textvariable=self.bind_port)
        combobox_bind_port['values'] = bind_port_history
        combobox_bind_port.grid(row=line, column=1, padx=5, pady=5, sticky=tk.N+tk.S+tk.W)
        combobox_bind_port.current(0)

        line += 1
        conn_port_history = ('dev://ttyACM0:115200', 'dev://ttyUSB0:115200', 'dev://COM11:115200', 'dev://COM12:115200', 'sim:', 'tcp://localhost:3333', 'tcp://192.168.3.163:3333')
        self.conn_port = tk.StringVar()
        lbl_svr_port = tk.Label(frame_svr, text=_("Connect to:"))
        lbl_svr_port.grid(row=line, column=0, padx=5, sticky=tk.N+tk.S+tk.W)
        combobox_conn_port = ttk.Combobox(frame_svr, textvariable=self.conn_port)
        combobox_conn_port['values'] = conn_port_history
        combobox_conn_port.grid(row=line, column=1, padx=5, pady=5, sticky=tk.N+tk.S+tk.W)
        combobox_conn_port.current(0)

        line -= 1
        self.btn_svr_start = tk.Button(frame_svr, text=_("Start"), command=self.do_start)
        self.btn_svr_start.grid(row=line, column=2, padx=5, sticky=tk.N+tk.S+tk.W+tk.E)
        #self.btn_svr_start.pack(side="right", fill="both", padx=5, pady=5, expand=True)

        line += 1
        self.btn_svr_stop = tk.Button(frame_svr, text=_("Stop"), command=self.do_stop)
        self.btn_svr_stop.grid(row=line, column=2, padx=5, sticky=tk.N+tk.S+tk.W+tk.E)
        #self.btn_svr_stop.pack(side="right", fill="both", padx=5, pady=5, expand=True)

        frame_svr.pack(side="top", fill="x", pady=10)

        self.text_log = None
        if config_use_textarea_log:
            self.text_log = tk.scrolledtext.ScrolledText(page_server, wrap=tk.WORD, height=1)
            self.text_log.configure(state='disabled')
            self.text_log.pack(expand=True, fill="both", side="top")
            #self.text_log.grid(row=line, column=1, columnspan=2, padx=5)
            self.text_log.bind("<1>", lambda event: self.text_log.focus_set()) # enable highlighting and copying
            #set_readonly_text(self.text_log, "Version Info\nver 1\nver 2\n")

            btn_log_clear = tk.Button(page_server, text=_("Clear"), command=lambda: (set_readonly_text(self.text_log, ""), self.text_log.update_idletasks()))
            #btn_log_clear.grid(row=line, column=0, columnspan=2, padx=5, sticky=tk.N+tk.S+tk.W+tk.E)
            btn_log_clear.pack(side="right", fill="both", padx=5, pady=5, expand=True)

        # page for client
        page_client = ttk.Frame(nb)
        lbl_cli_head = tk.Label(page_client, text=_("Test Client"), font=LARGE_FONT)
        lbl_cli_head.pack(side="top", fill="x", pady=10)

        frame_cli = ttk.LabelFrame(page_client, text=_("Connection"))

        line=0
        client_port_history = ('tcp://192.168.3.163:3333', 'dev://ttyACM0:115200', 'dev://ttyUSB0:115200', 'dev://COM11:115200', 'dev://COM12:115200', 'sim:', 'tcp://localhost:3333')
        self.client_port = tk.StringVar()
        lbl_cli_port = tk.Label(frame_cli, text=_("Connect to:"))
        lbl_cli_port.grid(row=line, column=0, padx=5, sticky=tk.N+tk.S+tk.W)
        combobox_client_port = ttk.Combobox(frame_cli, textvariable=self.client_port)
        combobox_client_port['values'] = client_port_history
        combobox_client_port.grid(row=line, column=1, padx=5, pady=5, sticky=tk.N+tk.S+tk.W)
        combobox_client_port.current(0)

        self.btn_cli_connect = tk.Button(frame_cli, text=_("Connect"), command=self.do_cli_connect)
        self.btn_cli_connect.grid(row=line, column=2, columnspan=1, padx=5, sticky=tk.N+tk.S+tk.W+tk.E)
        #self.btn_cli_connect.pack(side="left", fill="both", padx=5, pady=5, expand=True)

        self.btn_cli_disconnect = tk.Button(frame_cli, text=_("Disconnect"), command=self.do_cli_disconnect)
        self.btn_cli_disconnect.grid(row=line, column=3, columnspan=1, padx=5, sticky=tk.N+tk.S+tk.W+tk.E)
        #self.btn_cli_disconnect.pack(side="left", fill="both", padx=5, pady=5, expand=True)

        frame_cli.pack(side="top", fill="x", pady=10)

        page_command = page_client
        frame_top = tk.Frame(page_command)#, background="green")
        frame_bottom = tk.Frame(page_command)#, background="yellow")
        frame_top.pack(side="top", fill="both", expand=True)
        frame_bottom.pack(side="bottom", fill="x", expand=False)

        self.text_cli_command = ScrolledText(frame_top, wrap=tk.WORD)
        #self.text_cli_command.insert(tk.END, "Some Text\ntest 1\ntest 2\n")
        self.text_cli_command.configure(state='disabled')
        self.text_cli_command.pack(expand=True, fill="both", side="top")
        # make sure the widget gets focus when clicked
        # on, to enable highlighting and copying to the
        # clipboard.
        self.text_cli_command.bind("<1>", lambda event: self.text_cli_command.focus_set())

        btn_clear_cli_command = tk.Button(frame_bottom, text=_("Clear"), command=lambda: (set_readonly_text(self.text_cli_command, ""), self.text_cli_command.update_idletasks()) )
        btn_clear_cli_command.pack(side="left", fill="x", padx=5, pady=5, expand=False)
        self.cli_command = tk.StringVar()
        self.combobox_cli_command = ttk.Combobox(frame_bottom, textvariable=self.cli_command)
        self.combobox_cli_command['values'] = ('Help', 'GetAccel', 'GetButtons', 'GetCalInfo', 'GetCharger', 'GetDigitalSensors', 'GetErr', 'GetLDSScan', 'GetLifeStatLog', 'GetMotors', 'GetSchedule', 'GetTime', 'GetVersion', 'GetWarranty', 'PlaySound 0', 'Clean House', 'DiagTest MoveAndBump', 'DiagTest DropTest', 'RestoreDefaults', 'SetDistanceCal DropMinimum', 'SetFuelGauge Percent 100', 'SetIEC FloorSelection carpet', 'SetLCD BGWhite', 'SetLDSRotation On', 'SetLED BacklightOn', 'SetMotor VacuumOn', 'SetSchedule Day Sunday Hour 17 Min 0 House ON', 'SetSystemMode Shutdown', 'SetTime Day Sunday Hour 12 Min 5 Sec 25', 'SetWallFollower Enable', 'TestMode On', 'Upload' )
        self.combobox_cli_command.pack(side="left", fill="both", padx=5, pady=5, expand=True)
        self.combobox_cli_command.bind("<Return>", self.do_cli_run_ev)
        self.combobox_cli_command.bind("<<ComboboxSelected>>", self.do_select_clicmd)
        self.combobox_cli_command.current(0)
        btn_run_cli_command = tk.Button(frame_bottom, text=_("Run"), command=self.do_cli_run)
        btn_run_cli_command.pack(side="right", fill="x", padx=5, pady=5, expand=False)

        self.check_mid_cli_command()


        # last
        nb.add(page_server, text=_("Server"))
        nb.add(page_client, text=_("Test Client"))
        nb.add(page_about, text=_("About"))
        combobox_bind_port.focus()

        self.do_stop()
        self.do_cli_disconnect()
        return

    #
    # connection and command: support functions
    #
    def do_select_clicmd(self, event):
        self.combobox_cli_command.select_range(0, tk.END)
        return

    # the req is a list
    def cb_task_cli(self, tid, req):
        L.debug("do task: tid=" + str(tid) + ", req=" + str(req))
        reqstr = req[0]
        resp = self.serv_cli.get_request_block(reqstr)
        if resp != None:
            if resp.strip() != "":
                self.serv_cli.mailbox.put(req[1], resp.strip())
        return

    def do_cli_connect(self):
        self.do_cli_disconnect()
        L.info('client connect ...')
        L.info('connect to ' + self.client_port.get())
        self.serv_cli = neatocmdapi.NCIService(target=self.client_port.get().strip(), timeout=0.5)
        if self.serv_cli.open(self.cb_task_cli) == False:
            L.error ('Error in open serial')
            return
        self.mid_cli_command = self.serv_cli.mailbox.declair();
        L.info ('serial opened')
        self.btn_cli_connect.config(state=tk.DISABLED)
        self.btn_cli_disconnect.config(state=tk.NORMAL)
        return

    def do_cli_disconnect(self):
        if self.serv_cli != None:
            L.info('client disconnect ...')
            self.serv_cli.close()
        else:
            L.info('client is not connected, skip.')
        self.serv_cli = None
        self.mid_cli_command = -1;
        self.btn_cli_connect.config(state=tk.NORMAL)
        self.btn_cli_disconnect.config(state=tk.DISABLED)
        return

    def do_cli_run(self):
        if self.serv_cli == None:
            L.error('client is not connected, please connect it first!')
            return
        L.info('client run ...')
        reqstr = self.cli_command.get().strip()
        if reqstr != "":
            self.serv_cli.request([reqstr, self.mid_cli_command])
        return

    def do_cli_run_ev(self, event):
        self.do_cli_run()
        return

    def check_mid_cli_command(self):
        if self.serv_cli != None and self.mid_cli_command >= 0:
            try:
                resp = self.serv_cli.mailbox.get(self.mid_cli_command, False)
                respstr = resp.strip() + "\n\n"
                # put the content to the end of the textarea
                guilog.textarea_append (self.text_cli_command, respstr)
                self.text_cli_command.update_idletasks()
            except queue.Empty:
                # ignore
                pass
        # setup next
        self.after(300, self.check_mid_cli_command)
        return

def nxvforward_main():
    global config_use_textarea_log
    guilog.set_log_stderr()

    gettext_init()

    root = tk.Tk()
    root.title(str_progname + " - " + str_version)
    app = MyTkAppFrame(root)
    app.pack(fill="both", expand=True)
    ttk.Sizegrip(root).pack(side="right")

    if config_use_textarea_log:
        guilog.set_log_textarea (app.get_log_text())

    root.mainloop()

if __name__ == "__main__":
    nxvforward_main()

