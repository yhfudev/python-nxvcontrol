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

def set_log_stderr():
    logger = L.getLogger()
    formatter = L.Formatter('%(asctime)s %(levelname)s: %(message)s')

    console0 = L.StreamHandler()  # no arguments => stderr
    console0.setFormatter(formatter)
    logger.addHandler(console0)

def set_log_textarea(textarea):
    #L.basicConfig(level=L.DEBUG)
    logger = L.getLogger()
    formatter = L.Formatter('%(asctime)s %(levelname)s: %(message)s')

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


class ToggleButton(tk.Button):
    # txtt: the toggled text
    # txtr: the release text
    def __init__(self, master, txtt="toggled", txtr="released", imgt=None, imgr=None, command=None, *args, **kwargs):
        self.master = master
        self.command = command
        self.txtt = txtt
        self.txtr = txtr
        self.imgt = imgt
        self.imgr = imgr
        tk.Button.__init__(self, master, compound="left", command=self._command, relief="raised", text=self.txtr, image=self.imgr, *args, **kwargs)

        #perhaps set command event to send a message
        #self['command'] = lambda: self.message_upstream(Message(self.name, "I Got Clicked"))

        #do widget declarations
        #self.widgets = []

    def message_downstream(self, message):
        #for widget in self.widgets:
        #    widget.receive_message(message)
        pass

    def message_upstream(self, message):
        #self.master.message_upstream(self, message)
        pass

    def config(self, mapstr=None, relief=None, *args, **kwargs):
        if mapstr != None:
            return tk.Button.config(self, mapstr, *args, **kwargs)

        if relief != None:
            if relief=='sunken':
                return tk.Button.config(self, relief="sunken", text=self.txtt, image=self.imgt, *args, **kwargs)
            else:
                return tk.Button.config(self, relief="raised", text=self.txtr, image=self.imgr, *args, **kwargs)
        else:
            return tk.Button.config(self, *args, **kwargs)

    def _command(self):
        if tk.Button.config(self, 'relief')[-1] == 'sunken':
            tk.Button.config(self, relief="raised", text=self.txtr, image=self.imgr)
        else:
            tk.Button.config(self, relief="sunken", text=self.txtt, image=self.imgt)

        if self.command != None:
            self.command()
        pass

if __name__ == "__main__":
    root=tk.Tk()

    img_ledon=tk.PhotoImage(file="ledred-on.gif")
    img_ledoff=tk.PhotoImage(file="ledred-off.gif")

    def tracebtn():
        if b1.config('relief')[-1] == 'sunken':
            L.debug("pressed!")
        else:
            L.debug("released!")

    b1 = ToggleButton(root, txtt="ON", txtr="OFF", imgt=img_ledon, imgr=img_ledoff, command=tracebtn)
    b1.pack(pady=5)

    root.mainloop()
