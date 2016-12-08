#!/usr/bin/env python3

import os
import sys
if sys.version_info[0] < 3:
    import Tkinter as tk
    import ttk
    import ScrolledText
    import tkFileDialog as fd
else:
    import tkinter as tk
    from tkinter import ttk
    from tkinter.scrolledtext import ScrolledText
    import tkinter.filedialog as fd

import time
from threading import Thread
import queue


import logging as L
L.basicConfig(filename='serial.log', level=L.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

str_progname="TCPServer"
str_version="0.1"

LARGE_FONT= ("Verdana", 18)
NORM_FONT = ("Helvetica", 12)
SMALL_FONT = ("Helvetica", 8)

def textarea_append(text_area, msg):
    # Disabling states so no user can write in it
    text_area.configure(state=tk.NORMAL)
    text_area.insert(tk.END, msg) #Inserting the logger message in the widget
    text_area.configure(state=tk.DISABLED)
    text_area.see(tk.END)

# logging redirector
class IODirector(object):
    def __init__(self, text_area):
        self.text_area = text_area
class TextareaStream(IODirector):
    def write(self, msg):
        # Disabling states so no user can write in it
        textarea_append(self.text_area, msg)
    def flush(self):
        pass
class TextareaLogHandler(L.StreamHandler):
    def __init__(self, textctrl):
        L.StreamHandler.__init__(self) # initialize parent
        self.text_area = textctrl
        self.text_area.tag_config("INFO", foreground="black")
        self.text_area.tag_config("DEBUG", foreground="grey")
        self.text_area.tag_config("WARNING", foreground="orange")
        self.text_area.tag_config("ERROR", foreground="red")
        self.text_area.tag_config("CRITICAL", foreground="red", underline=1)

    # for logging.StreamHandler
    def emit(self, record):
        textarea_append(self.text_area, self.format(record) + "\n")

def set_log_textarea(textarea):
    #L.basicConfig(level=L.DEBUG)
    logger = L.getLogger()
    formatter = L.Formatter('%(asctime)s %(levelname)s: %(message)s')

    console0 = L.StreamHandler()  # no arguments => stderr
    console0.setFormatter(formatter)
    logger.addHandler(console0)
    if 1 == 2:
        handler = TextareaStream(textarea)
        console = L.StreamHandler(handler)
        #console.setFormatter(formatter)
        logger.addHandler(console)
    else:
        console2 = TextareaLogHandler(textarea)
        console2.setFormatter(formatter)
        logger.addHandler(console2)

    L.info("set logger done")
    L.debug("debug test 1")


def set_readonly_text(text, msg):
    text.config(state=tk.NORMAL)
    text.delete(1.0, tk.END)
    text.insert(tk.END, msg)
    text.config(state=tk.DISABLED)

class MyTkAppFrame(ttk.Notebook):

    def do_stop(self):
        if self.runT != None:
            if self.runT.isAlive():
                L.info('signal server to stop ...')
                self.server.shutdown()
                self.server.server_close()
                return
        L.info('server is not running. skip')
        return

    def do_start(self):
        import socketserver as ss
        import neatocmdsim as nsim

        class ThreadedTCPRequestHandler(ss.BaseRequestHandler):
            # override base class handle method
            def handle(self):
                BUFFER_SIZE = 4096
                MAXIUM_SIZE = BUFFER_SIZE * 5
                data = ""
                L.info("server connectd by client: " + str(self.client_address))
                cli_log_head = "CLI" + str(self.client_address)
                while 1:
                    recvdat = self.request.recv(BUFFER_SIZE)
                    if not recvdat:
                        # EOF, client closed, just return
                        L.info(cli_log_head + " disconnected: " + str(self.client_address))
                        return
                    data += str(recvdat, 'ascii')
                    L.debug(cli_log_head + " all of data: " + data)
                    cntdata = data.count('\n')
                    L.debug(cli_log_head + " the # of newline: %d"%cntdata)
                    if (cntdata < 1):
                        L.debug(cli_log_head + " not receive newline, skip: " + data)
                        continue
                    requests = data.split('\n')
                    for i in range(0, cntdata):
                        request = requests[i].strip()
                        L.info(cli_log_head + " request [" + str(i+1) + "/" + str(cntdata) + "]" + request)
                        response = nsim.fake_respose(request)
                        if response != "":
                            self.request.sendall(response)
                    data = requests[-1]

        class ThreadedTCPServer(ss.ThreadingMixIn, ss.TCPServer):
            daemon_threads = True
            allow_reuse_address = True
            pass

        if self.runT != None:
            if self.runT.isAlive():
                L.info('server is already running. skip')
                return

        L.info('start server ' + self.chistory.get())
        b = self.chistory.get().split(":")
        HOST=b[0]
        PORT=3333
        if len(b) > 1:
            PORT=int(b[1])
        L.info('server is running ...')
        try:
            self.server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
        except Exception as e:
            L.error("Error in starting service: " + str(e))
            return
        ip, port = self.server.server_address
        L.info("server listened to: " + str(ip) + ":" + str(port))
        self.runT = Thread(target=self.server.serve_forever)
        self.runT.setDaemon(True) # When closing the main thread, which is our GUI, all daemons will automatically be stopped as well.
        self.runT.start()
        return

    def get_log_text(self):
        return self.text_log

    def __init__(self, tk_frame_parent):
        ttk.Notebook.__init__(self, tk_frame_parent)
        nb = self
        self.runT = None

        # page for About
        page_about = ttk.Frame(nb)
        lbl_about_head = tk.Label(page_about, text="About", font=LARGE_FONT)
        lbl_about_head.pack(side="top", fill="x", pady=10)
        lbl_about_main = tk.Label(page_about, text="\n" + str_progname + "\n" + str_version + "\n" + """
TCP Echo Server

Copyright © 2015–2016 The NeatoSetup Authors

This program comes with absolutely no warranty.
See the GNU General Public License, version 2 or later for details.""", font=NORM_FONT)
        lbl_about_main.pack(side="top", fill="x", pady=10)

        # page for server
        page_server = ttk.Frame(nb)
        lbl_svr_head = tk.Label(page_server, text="Server", font=LARGE_FONT)
        lbl_svr_head.pack(side="top", fill="x", pady=10)

        frame_svr = ttk.LabelFrame(page_server, text='Setup')

        commandhistory = ('localhost:3333', '127.0.0.1:4444', 'localhost:5555')
        self.chistory = tk.StringVar()
        line=0
        lbl_svr_port = tk.Label(frame_svr, text="Bind Address:")
        lbl_svr_port.grid(row=line, column=0, padx=5, sticky=tk.N+tk.S+tk.W)
        combobox_chistory = ttk.Combobox(frame_svr, textvariable=self.chistory)
        combobox_chistory['values'] = commandhistory
        combobox_chistory.grid(row=line, column=1, padx=5, pady=5, sticky=tk.N+tk.S+tk.W)
        combobox_chistory.current(0)

        frame_svr.pack(side="top", fill="x", pady=10)

        self.text_log = tk.scrolledtext.ScrolledText(page_server, wrap=tk.WORD, height=1)
        self.text_log.configure(state='disabled')
        self.text_log.pack(expand=True, fill="both", side="top")
        #self.text_log.grid(row=line, column=1, columnspan=2, padx=5)
        self.text_log.bind("<1>", lambda event: self.text_log.focus_set()) # enable highlighting and copying
        #set_readonly_text(self.text_log, "Version Info\nver 1\nver 2\n")

        btn_svr_start = tk.Button(page_server, text="Start", command=self.do_start)
        #btn_svr_start.grid(row=line, column=0, columnspan=2, padx=5, sticky=tk.N+tk.S+tk.W+tk.E)
        btn_svr_start.pack(side="left", fill="both", padx=5, pady=5, expand=True)

        btn_svr_stop = tk.Button(page_server, text="Stop", command=self.do_stop)
        #btn_svr_stop.grid(row=line, column=0, columnspan=2, padx=5, sticky=tk.N+tk.S+tk.W+tk.E)
        btn_svr_stop.pack(side="left", fill="both", padx=5, pady=5, expand=True)

        # page for client
        page_client = ttk.Frame(nb)
        lbl_cli_head = tk.Label(page_client, text="Client", font=LARGE_FONT)
        lbl_cli_head.pack(side="top", fill="x", pady=10)
        #page_client = page_server # debug!

        # last
        nb.add(page_server, text='Server')
        nb.add(page_client, text='Client')
        nb.add(page_about, text='About')
        combobox_chistory.focus()

def demo():

    root = tk.Tk()
    root.title(str_progname + " - " + str_version)
    app = MyTkAppFrame(root)
    app.pack(fill="both", expand=True)
    ttk.Sizegrip(root).pack(side="right")

    set_log_textarea (app.get_log_text())

    root.mainloop()

if __name__ == "__main__":
    demo()

