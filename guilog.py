#!/usr/bin/python3

import sys
if sys.version_info[0] < 3:
    import Tkinter as tk
    import ttk

else:
    import tkinter as tk
    from tkinter import ttk

import logging as L

def textarea_append(text_area, msg):
    # Disabling states so no user can write in it
    text_area.configure(state=tk.NORMAL)
    text_area.insert(tk.END, msg) #Inserting the logger message in the widget
    text_area.configure(state=tk.DISABLED)
    text_area.see(tk.END)
    #text_area.update_idletasks()

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

