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

str_progname="NeatoSetup"
str_version="0.1"

LARGE_FONT= ("Verdana", 18)
NORM_FONT = ("Helvetica", 12)
SMALL_FONT = ("Helvetica", 8)


# TODO:
#   the background thread to handle the communication with the neato
#   a request scheduler is used because of the serial port
#   the scheduler supports the time tagged request which is executed at the exact time
#   the scheduler supports the the requst which has no required time, it will executed at the idle time
#   a request contains the exact time tag, repeat time, user data, callback?
#   return the result, execute start time, execute end time,



def test_pack(main_container):
    main_container.pack(side="top", fill="both", expand=True)
    top_frame = tk.Frame(main_container, background="green")
    bottom_frame = tk.Frame(main_container, background="yellow")
    top_frame.pack(side="top", fill="x", expand=False)
    bottom_frame.pack(side="bottom", fill="both", expand=True)

    top_left = tk.Frame(top_frame, background="pink")
    top_center = tk.Frame(top_frame, background="red")
    top_right = tk.Frame(top_frame, background="blue")
    top_left.pack(side="left", fill="x", expand=True)
    top_center.pack(side="left", fill="x", expand=True)
    top_right.pack(side="right", fill="x", expand=True)

    top_left_label = tk.Label(top_left, text="Top Left")
    top_center_label = tk.Label(top_center, text="Top Center")
    top_right_label = tk.Label(top_right, text="Top Right")
    top_left_label.pack(side="left")
    top_center_label.pack(side="top")
    top_right_label.pack(side="right")

    text_box = tk.Text(bottom_frame, height=5, width=40, background="gray")
    text_box.pack(side="top", fill="both", expand=True)


def test_grid(myParent, main_container):
    main_container.grid(row=0, column=0, sticky="nsew")
    myParent.grid_rowconfigure(0, weight=1)
    myParent.grid_columnconfigure(0, weight=1)
    top_frame = tk.Frame(main_container, background="green")
    bottom_frame = tk.Frame(main_container, background="yellow")
    top_frame.grid(row=0, column=0, sticky="ew")
    bottom_frame.grid(row=1, column=0,sticky="nsew")
    main_container.grid_rowconfigure(1, weight=1)
    main_container.grid_columnconfigure(0, weight=1)
    top_left = tk.Frame(top_frame, background="pink")
    top_center = tk.Frame(top_frame, background="red")
    top_right = tk.Frame(top_frame, background="blue")
    top_left.grid(row=0, column=0, sticky="w")
    top_center.grid(row=0, column=1)
    top_right.grid(row=0, column=2, sticky="e")
    top_frame.grid_columnconfigure(1, weight=1)
    top_left_label = tk.Label(top_left, text="Top Left")
    top_center_label = tk.Label(top_center, text="Top Center")
    top_right_label = tk.Label(top_right, text="Top Right")
    top_left_label.grid(row=0, column=0, sticky="w")
    top_center_label.grid(row=0, column=0)
    top_right_label.grid(row=0, column=0, sticky="e")

def set_readonly_text(text, msg):
    text.config(state=tk.NORMAL)
    text.delete(1.0, tk.END)
    text.insert(tk.END, msg)
    text.config(state=tk.DISABLED)

class MyTkAppFrame(ttk.Notebook): #(tk.Frame):
    def set_battery_level(self, level):
        self.style_battstat.configure("LabeledProgressbar", text="{0} %      ".format(level))
        self.progress_batt["value"]=level
        #self.frame_status.update()

    def set_robot_version(self, msg):
        set_readonly_text(self.text_version, msg)

    # the functions for log file in status
    def onSelectAllLogname(self, event):
        self.combobox_logfile.tag_add(tk.SEL, "1.0", tk.END)
        self.combobox_logfile.mark_set(tk.INSERT, "1.0")
        self.combobox_logfile.see(tk.INSERT)
        return 'break'

    def onLogfileCheckChanged(self):
        # read self.use_logfile changed by self.check_logfile
        # check if the file exists
        # start to log
        return


    def onLogfileSelected(self, event):
        # read self.use_logfile changed by self.check_logfile
        # change log file
        return

    def onSelectLogfile(self):
        #dir_path = os.path.dirname(os.path.realpath(__file__))
        pname_input = self.combobox_logfile.get().strip()
        dir_path=os.path.dirname(os.path.realpath(pname_input))
        if True != os.path.exists(dir_path):
            dir_path = os.getcwd()
        fname = fd.askopenfilename(
                              initialdir=dir_path,
                              filetypes=(
                                            ("Text files", "*.txt"),
                                            ("All files", "*.*")
                                        )
                                  )
        if fname:
            self.combobox_logfile.set(fname.strip())
        return

    def __init__(self, tk_frame_parent):
        #nb = ttk.Notebook(tk_frame_parent)
        ttk.Notebook.__init__(self, tk_frame_parent)
        nb = self

        # page for test pack()
        page_testpack = tk.Frame(nb)
        #lbl_test_head = tk.Label(page_testpack, text="Test pack()", font=LARGE_FONT)
        #lbl_test_head.pack(side="top", fill="x", pady=10)
        #main_container = page_testpack
        test_pack(page_testpack)

        # page for test grid
        #page_testgrid = tk.Frame(nb)
        #myParent = nb
        #main_container = page_testgrid
        #test_grid(myParent, main_container)

        # page for About
        page_about = ttk.Frame(nb)
        lbl_about_head = tk.Label(page_about, text="About", font=LARGE_FONT)
        lbl_about_head.pack(side="top", fill="x", pady=10)
        lbl_about_main = tk.Label(page_about, text="\n" + str_progname + "\n" + str_version + "\n" + """
Setup your Neato Robot

Copyright © 2015–2016 The NeatoSetup Authors

This program comes with absolutely no warranty.
See the GNU General Public License, version 2 or later for details.""", font=NORM_FONT)
        lbl_about_main.pack(side="top", fill="x", pady=10)

        # adding Frames as pages for the ttk.Notebook 
        # first page, which would get widgets gridded into it
        page_conn = ttk.Frame(nb)
        # includes:
        #   connect with port selection or Serial-TCP connection;
        #   button to shutdown
        #   testmode indicator and button to enter/leave test mode
        #   the robot time, sync with pc
        #   textarea of version info
        #   log file name, enable/disable: all of connection message and input output will be here!
        lbl_conn_head = tk.Label(page_conn, text="Connection", font=LARGE_FONT)
        lbl_conn_head.pack(side="top", fill="x", pady=10)
        f1 = ttk.LabelFrame(page_conn, text='Conection')
        self.frame_status = ttk.LabelFrame(page_conn, text='Status')

        # connection
        portnames = ('tcp://localhost:3333', '/dev/ttyACM0', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'COM10', )
        pnames = tk.StringVar(value=portnames)
        #text_conn = tk.Text(f1, height=1)
        #text_conn.pack(side="top", fill="x", padx=5, pady=5, expand=True)
        selnames = tk.StringVar()
        combobox_conn = ttk.Combobox(f1, textvariable=selnames)
        #combobox_conn.bind('<<ComboboxSelected>>', cb_function)
        combobox_conn['values'] = ('USA', 'Canada', 'Australia')
        combobox_conn.pack(side="top", fill="x", padx=5, pady=5, expand=True)
        lbox_conn = tk.Listbox(f1, listvariable=pnames, height=10)
        lbox_conn.pack(side="left", fill="x", padx=5, pady=5, expand=True)
        scroll_conn = ttk.Scrollbar(f1, orient=tk.VERTICAL, command=lbox_conn.yview)
        scroll_conn.pack(side="left", fill="y", padx=5, pady=5, expand=False)
        #scroll_conn.pack(side=tk.RIGHT, fill=tk.Y)
        lbox_conn.configure(yscrollcommand=scroll_conn.set)
        btn_conn = tk.Button(f1, text="Connect")
        btn_conn.pack(side="top", fill="y", padx=5, pady=5, expand=False)
        btn_disconn = tk.Button(f1, text="Disconnect")
        btn_disconn.pack(side="bottom", fill="y", padx=5, pady=5, expand=False)

        # status
        line = 0 # line
        lbl_synctime_conn = tk.Label(self.frame_status, text="Robot Time:")
        lbl_synctime_conn.grid(row=line, column=0, padx=5, sticky=tk.N+tk.S+tk.W)
        lbl_synctime = tk.Label(self.frame_status, text="00:00:00")
        lbl_synctime.grid(row=line, column=1, padx=5)
        #lbl_synctime.pack(side="right", fill="x", pady=10)
        btn_synctime = tk.Button(self.frame_status, text="Sync PC time to robot")
        btn_synctime.grid(row=line, column=2, padx=5, sticky=tk.N+tk.S+tk.E+tk.W)
        #btn_synctime.pack(side="right", fill="x", pady=10)
        line += 1
        lbl_testmode_conn = tk.Label(self.frame_status, text="Test Mode:")
        lbl_testmode_conn.grid(row=line, column=0, padx=5)
        lbl_testmode = tk.Label(self.frame_status, text="Unknown")
        lbl_testmode.grid(row=line, column=1, padx=5)
        btn_testmode_on = tk.Button(self.frame_status, text="Test ON")
        btn_testmode_off = tk.Button(self.frame_status, text="Test OFF")
        btn_testmode_on.grid(row=line, column=2, padx=5, sticky=tk.N+tk.S+tk.W)
        btn_testmode_off.grid(row=line, column=2, padx=5, sticky=tk.N+tk.S+tk.E)
        line += 1
        lbl_battstat_conn = tk.Label(self.frame_status, text="Battery Status:")
        lbl_battstat_conn.grid(row=line, column=0, padx=5)
        self.style_battstat = ttk.Style(self.frame_status)
        # add the label to the progressbar style
        self.style_battstat.layout("LabeledProgressbar",
                [('LabeledProgressbar.trough',
                {'children': [('LabeledProgressbar.pbar',
                                {'side': 'left', 'sticky': 'ns'}),
                                ("LabeledProgressbar.label",
                                {"sticky": ""})],
                'sticky': 'nswe'})])
        self.progress_batt = ttk.Progressbar(self.frame_status, orient=tk.HORIZONTAL, style="LabeledProgressbar", mode='determinate', length=300)
        self.progress_batt.grid(row=line, column=1, padx=5)
        #self.set_battery_level(50)
        #btn_battstat = tk.Button(self.frame_status, text="")
        #btn_battstat.grid(row=line, column=2, padx=5, sticky=tk.E)
        line += 1
        lbl_battstat_conn = tk.Label(self.frame_status, text="Version:")
        lbl_battstat_conn.grid(row=line, column=0, padx=5)
        self.text_version = ScrolledText(self.frame_status, wrap=tk.WORD, height=10)
        self.text_version.configure(state='disabled')
        #self.text_version.pack(expand=True, fill="both", side="top")
        self.text_version.grid(row=line, column=1, columnspan=2, padx=5)
        self.text_version.bind("<1>", lambda event: text_command.focus_set()) # enable highlighting and copying
        self.set_robot_version("Version Info\nver 1\nver 2\n")
        line += 1
        self.use_logfile = tk.StringVar()
        self.check_logfile = ttk.Checkbutton(self.frame_status, text='Use Log File',
            command=self.onLogfileCheckChanged, variable=self.use_logfile,
            onvalue='metric', offvalue='imperial')
        self.check_logfile.grid(row=line, column=0, padx=5)
        sellogfiles = tk.StringVar()
        self.combobox_logfile = ttk.Combobox(self.frame_status, textvariable=sellogfiles)
        self.combobox_logfile.bind('<<ComboboxSelected>>', self.onLogfileSelected)
        self.combobox_logfile.bind("<Control-Key-a>", self.onSelectAllLogname)
        self.combobox_logfile.bind("<Control-Key-A>", self.onSelectAllLogname)
        self.combobox_logfile['values'] = ('neatologfile.txt', '/tmp/neatologfile.txt', '$HOME/logfile.txt')
        self.combobox_logfile.current(0)
        self.combobox_logfile.grid(row=line, column=1, sticky=tk.W+tk.E)
        self.button_select_logfile = tk.Button(self.frame_status, text=" ... ", command=self.onSelectLogfile)
        self.button_select_logfile.grid(row=line, column=2, sticky=tk.W)

        f1.pack(side="top", fill="x", pady=10)
        self.frame_status.pack(side="top", fill="both", pady=10)

        #ttk.Separator(page_conn, orient=HORIZONTAL).pack()
        #b1 = tk.Button(page_about, text="Button 1")

        # page for commands
        page_command = ttk.Frame(nb)
        #   combox list for all available know commands, select one will show the help message in text area
        #   edit line which supports history
        #   output
        #   help message area
        lbl_command_head = tk.Label(page_command, text="Commands", font=LARGE_FONT)
        lbl_command_head.pack(side="top", fill="x", pady=10)
        commandhistory = ('GetCharger')
        chistory = tk.StringVar(value=commandhistory)

        frame_top = tk.Frame(page_command)#, background="green")
        frame_bottom = tk.Frame(page_command)#, background="yellow")
        frame_top.pack(side="top", fill="both", expand=True)
        frame_bottom.pack(side="bottom", fill="x", expand=False)

        text_command = ScrolledText(frame_top, wrap=tk.WORD)
        text_command.insert(tk.END, "Some Text\ntest 1\ntest 2\n")
        text_command.configure(state='disabled')
        text_command.pack(expand=True, fill="both", side="top")
        # make sure the widget gets focus when clicked
        # on, to enable highlighting and copying to the
        # clipboard.
        text_command.bind("<1>", lambda event: text_command.focus_set())

        combobox_chistory = ttk.Combobox(frame_bottom, textvariable=chistory)
        combobox_chistory['values'] = ('GetCharger', 'GetTime', 'GetVersion')
        combobox_chistory.pack(side="left", fill="both", padx=5, pady=5, expand=True)
        btn_command = tk.Button(frame_bottom, text="Run")
        btn_command.pack(side="right", fill="x", padx=5, pady=5, expand=False)


#    txt_about = tk.Text(page_about)
#    scroll_about = tk.Scrollbar(page_about, command=txt_about.yview)
#    txt_about.configure(yscrollcommand=scroll_about.set)
#    txt_about.tag_configure('bold_italics', font=('Arial', 12, 'bold', 'italic'))
#    txt_about.tag_configure('big', font=('Verdana', 20, 'bold'))
#    txt_about.tag_configure('color', foreground='#476042', font=('Tempus Sans ITC', 12, 'bold'))
#    txt_about.insert(tk.END,'\n' + str_progname + '\n', 'big')
#
#    txt_about.insert(tk.END,"""
#        Setup your Neato Robot
#
#        Copyright © 2015–2016 The NeatoSetup Authors
#
#        This program comes with absolutely no warranty.
#        See the GNU General Public License, version 2 or later for details.""", 'color')
#    txt_about.pack(side=tk.LEFT)
#    scroll_about.pack(side=tk.RIGHT, fill=tk.Y)

        # page for scheduler
        page_sche = ttk.Frame(nb)
        #   indicator, enable/disable button
        #   save/load file
        #   the list of scheduler
        lbl_sche_head = tk.Label(page_sche, text="Schedule", font=LARGE_FONT)
        lbl_sche_head.pack(side="top", fill="x", pady=10)

        # page for sensors
        page_sensors = ttk.Frame(nb)
        #   the list of sensor status, includes sensor and value
        #   indicator of testmode, no control
        #   indicator, enable/disable auto update
        lbl_sensor_head = tk.Label(page_sensors, text="Sensors", font=LARGE_FONT)
        lbl_sensor_head.pack(side="top", fill="x", pady=10)

        # page for LiDAR
        page_lidar = ttk.Frame(nb)
        #   graph for current data
        #   indicator, enable/disable scanning
        #   buttons to remote control: left/right/up/down/rotate
        lbl_lidar_head = tk.Label(page_lidar, text="LiDAR", font=LARGE_FONT)
        lbl_lidar_head.pack(side="top", fill="x", pady=10)

        # page for motors
        page_moto = ttk.Frame(nb)
        #   list of motors and each has indicator, start/stop button
        #   warnning message: flip the robot upside down so the wheels are faceing up, before enable wheels moto!
        lbl_moto_head = tk.Label(page_moto, text="Motors", font=LARGE_FONT)
        lbl_moto_head.pack(side="top", fill="x", pady=10)
        s = ttk.Scale(page_moto, orient=tk.HORIZONTAL, length=200, from_=1.0, to=100.0)

        # page for LifeStatLog
        page_statlog = ttk.Frame(nb)
        #   list of motors and each has indicator, start/stop button
        #   warnning message: flip the robot upside down so the wheels are faceing up, before enable wheels moto!
        lbl_statlog_head = tk.Label(page_statlog, text="LifeStatLog", font=LARGE_FONT)
        lbl_statlog_head.pack(side="top", fill="x", pady=10)

        text_statlog = ScrolledText(page_statlog, wrap=tk.WORD)
        text_statlog.insert(tk.END, "Some Text\ntest 1\ntest 2\n")
        text_statlog.configure(state='disabled')
        text_statlog.pack(expand=True, fill="both", side="top")
        text_statlog.bind("<1>", lambda event: text_statlog.focus_set())

        btn_statlog_get = tk.Button(page_statlog, text="Get Log")
        btn_statlog_get.pack(side=tk.BOTTOM)

        # page for Recharge
        page_recharge = ttk.Frame(nb)
        # only available when connected to Serial port directly, not for TCP
        lbl_recharge_head = tk.Label(page_recharge, text="Recharge", font=LARGE_FONT)
        lbl_recharge_head.pack(side="top", fill="x", pady=10)

        nb.add(page_conn, text='Connection')
        nb.add(page_command, text='Commands')
        nb.add(page_sche, text='Schedule')
        nb.add(page_sensors, text='Sensors')
        nb.add(page_lidar, text='LiDAR')
        nb.add(page_moto, text='Moto')
        nb.add(page_statlog, text='LifeStatLog')
        nb.add(page_recharge, text='Recharge')
        nb.add(page_about, text='About')
        #nb.add(page_testgrid, text='TestGrid')
        nb.add(page_testpack, text='TestPack')


def demo():
    root = tk.Tk()
    root.title(str_progname + " - " + str_version)

    #nb.pack(expand=1, fill="both")
    MyTkAppFrame(root).pack(fill="both", expand=True)
    #ttk.Sizegrip(root).grid(column=999, row=999, sticky=(tk.S,tk.E))
    ttk.Sizegrip(root).pack(side="right")
    root.mainloop()


if __name__ == "__main__":
    demo()
















