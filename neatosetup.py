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

import queue

import logging as L
L.basicConfig(filename='neatosetup.log', level=L.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

import neatocmdapi
import guilog

str_progname="NeatoSetup"
str_version="0.1"

LARGE_FONT= ("Verdana", 18)
NORM_FONT = ("Helvetica", 12)
SMALL_FONT = ("Helvetica", 8)

# key for state machine wheel
KEY_NONE=0
KEY_LEFT=1
KEY_RIGHT=2
KEY_UP=3
KEY_DOWN=4
KEY_BACK=5
# the states
STATE_STOP=1
STATE_FORWARD=2
STATE_BACK=3
STATE_LEFT=4
STATE_RIGHT=5

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

import math
# const
MAXDIST=16700 # the maxmium allowed of the distance value of lidar
MAXDIST=4000 # the maxmium allowed of the distance value of lidar
CONST_RAD=math.pi / 180

class MyTkAppFrame(ttk.Notebook): #(tk.Frame):
    def show_battery_level(self, level):
        self.style_battstat.configure("LabeledProgressbar", text="{0} %      ".format(level))
        self.progress_batt["value"]=level
        #self.frame_status.update()
        #self.progress_batt.update_idletasks()

    def show_robot_version(self, msg):
        if msg.find("GetVersion") >= 0:
            set_readonly_text(self.text_version, msg)
        else:
            guilog.textarea_append(self.text_version, "\n\n" + msg)

    def show_robot_time(self, msg):
        self.lbl_synctime['text'] = msg

    def show_robot_testmode(self, onoff=False):
        if onoff:
            self.lbl_testmode['text'] = "ON"
            self.lbl_testmode['fg'] = "red"
        else:
            self.lbl_testmode['text'] = "OFF"
            self.lbl_testmode['fg'] = "green"

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
        global MAXDIST
        global CONST_RAD
        #nb = ttk.Notebook(tk_frame_parent)
        ttk.Notebook.__init__(self, tk_frame_parent)
        nb = self
        self.serv_cli = None
        self.istestmode = False

        # the images for toggle buttons
        self.img_ledon=tk.PhotoImage(file="ledred-on.gif")
        self.img_ledoff=tk.PhotoImage(file="ledred-off.gif")

        guilog.rClickbinder(tk_frame_parent)

        # page for test pack()
        #page_testpack = tk.Frame(nb)
        #test_pack(page_testpack)

        # page for test grid
        #page_testgrid = tk.Frame(nb)
        #myParent = nb
        #main_container = page_testgrid
        #test_grid(myParent, main_container)

        # page for About
        page_about = tk.Frame(nb)
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
        page_conn = tk.Frame(nb)
        # includes:
        #   connect with port selection or Serial-TCP connection;
        #   button to shutdown
        #   testmode indicator and button to enter/leave test mode
        #   the robot time, sync with pc
        #   textarea of version info
        #   log file name, enable/disable: all of connection message and input output will be here!
        lbl_conn_head = tk.Label(page_conn, text="Connection", font=LARGE_FONT)
        lbl_conn_head.pack(side="top", fill="x", pady=10)
        self.frame_status = ttk.LabelFrame(page_conn, text='Status')


        # connection
        frame_cli = ttk.LabelFrame(page_conn, text='Conection')
        line=0
        client_port_history = ('tcp://192.168.3.163:3333', 'dev://ttyACM0:115200', 'dev://ttyUSB0:115200', 'dev://COM11:115200', 'dev://COM12:115200', 'sim:', 'tcp://localhost:3333')
        self.client_port = tk.StringVar()
        lbl_cli_port = tk.Label(frame_cli, text="Connect to:")
        lbl_cli_port.grid(row=line, column=0, padx=5, sticky=tk.N+tk.S+tk.W)
        combobox_client_port = ttk.Combobox(frame_cli, textvariable=self.client_port)
        combobox_client_port['values'] = client_port_history
        combobox_client_port.grid(row=line, column=1, padx=5, pady=5, sticky=tk.N+tk.S+tk.W)
        combobox_client_port.current(0)
        # Buttons
        self.btn_cli_connect = tk.Button(frame_cli, text="Connect", command=self.do_cli_connect)
        self.btn_cli_connect.grid(row=line, column=2, columnspan=1, padx=5, sticky=tk.N+tk.S+tk.W+tk.E)
        #btn_cli_connect.pack(side="left", fill="both", padx=5, pady=5, expand=True)
        self.btn_cli_disconnect = tk.Button(frame_cli, text="Disconnect", state=tk.DISABLED, command=self.do_cli_disconnect)
        self.btn_cli_disconnect.grid(row=line, column=3, columnspan=1, padx=5, sticky=tk.N+tk.S+tk.W+tk.E)
        #btn_cli_disconnect.pack(side="left", fill="both", padx=5, pady=5, expand=True)
        frame_cli.pack(side="top", fill="x", pady=10)

        self.status_isactive = False # shall we refresh the time and battery info?

        # status
        line = 0 # line
        lbl_synctime_conn = tk.Label(self.frame_status, text="Robot Time:")
        lbl_synctime_conn.grid(row=line, column=0, padx=5, sticky=tk.N+tk.S+tk.W)
        self.lbl_synctime = tk.Label(self.frame_status, text="00:00:00")
        self.lbl_synctime.grid(row=line, column=1, padx=5)
        #self.lbl_synctime.pack(side="right", fill="x", pady=10)
        btn_synctime = tk.Button(self.frame_status, text="Sync PC time to robot", command=self.set_robot_time_from_pc)
        btn_synctime.grid(row=line, column=2, padx=5, sticky=tk.N+tk.S+tk.E+tk.W)
        #btn_synctime.pack(side="right", fill="x", pady=10)
        line += 1
        lbl_testmode_conn = tk.Label(self.frame_status, text="Test Mode:")
        lbl_testmode_conn.grid(row=line, column=0, padx=5)
        self.lbl_testmode = tk.Label(self.frame_status, text="Unknown")
        self.lbl_testmode.grid(row=line, column=1, padx=5)
        btn_testmode_on = tk.Button(self.frame_status, text="Test ON", command=lambda: self.set_robot_testmode(True))
        btn_testmode_off = tk.Button(self.frame_status, text="Test OFF", command=lambda: self.set_robot_testmode(False))
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
        #btn_battstat = tk.Button(self.frame_status, text="")
        #btn_battstat.grid(row=line, column=2, padx=5, sticky=tk.E)
        line += 1
        lbl_battstat_conn = tk.Label(self.frame_status, text="Version:")
        lbl_battstat_conn.grid(row=line, column=0, padx=5)
        self.text_version = ScrolledText(self.frame_status, wrap=tk.WORD, height=10)
        self.text_version.configure(state='disabled')
        #self.text_version.pack(expand=True, fill="both", side="top")
        self.text_version.grid(row=line, column=1, columnspan=2, padx=5)
        self.text_version.bind("<1>", lambda event: self.text_version.focus_set()) # enable highlighting and copying

        # save log file?
        #line += 1
        #self.use_logfile = tk.StringVar()
        #self.check_logfile = ttk.Checkbutton(self.frame_status, text='Use Log File',
            #command=self.onLogfileCheckChanged, variable=self.use_logfile,
            #onvalue='metric', offvalue='imperial')
        #self.check_logfile.grid(row=line, column=0, padx=5)
        #sellogfiles = tk.StringVar()
        #self.combobox_logfile = ttk.Combobox(self.frame_status, textvariable=sellogfiles)
        #self.combobox_logfile.bind('<<ComboboxSelected>>', self.onLogfileSelected)
        #self.combobox_logfile.bind("<Control-Key-a>", self.onSelectAllLogname)
        #self.combobox_logfile.bind("<Control-Key-A>", self.onSelectAllLogname)
        #self.combobox_logfile['values'] = ('neatologfile.txt', '/tmp/neatologfile.txt', '$HOME/logfile.txt')
        #self.combobox_logfile.current(0)
        #self.combobox_logfile.grid(row=line, column=1, sticky=tk.W+tk.E)
        #self.button_select_logfile = tk.Button(self.frame_status, text=" ... ", command=self.onSelectLogfile)
        #self.button_select_logfile.grid(row=line, column=2, sticky=tk.W)

        frame_cli.pack(side="top", fill="x", pady=10)
        self.frame_status.pack(side="top", fill="both", pady=10)

        #ttk.Separator(page_conn, orient=HORIZONTAL).pack()
        #b1 = tk.Button(page_about, text="Button 1")

        # page for commands
        page_command = tk.Frame(nb)
        #   combox list for all available know commands, select one will show the help message in text area
        #   edit line which supports history
        #   output
        #   help message area
        lbl_command_head = tk.Label(page_command, text="Commands", font=LARGE_FONT)
        lbl_command_head.pack(side="top", fill="x", pady=10)

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

        btn_clear_cli_command = tk.Button(frame_bottom, text="Clear", command=lambda: (set_readonly_text(self.text_cli_command, ""), self.text_cli_command.update_idletasks()) )
        btn_clear_cli_command.pack(side="left", fill="x", padx=5, pady=5, expand=False)
        self.cli_command = tk.StringVar()
        self.combobox_cli_command = ttk.Combobox(frame_bottom, textvariable=self.cli_command)
        self.combobox_cli_command['values'] = ('Help', 'GetAccel', 'GetButtons', 'GetCalInfo', 'GetCharger', 'GetDigitalSensors', 'GetErr', 'GetLDSScan', 'GetLifeStatLog', 'GetMotors', 'GetSchedule', 'GetTime', 'GetVersion', 'GetWarranty', 'PlaySound 0')
        self.combobox_cli_command.pack(side="left", fill="both", padx=5, pady=5, expand=True)
        self.combobox_cli_command.bind("<Return>", self.do_cli_run_ev)
        self.combobox_cli_command.bind("<<ComboboxSelected>>", self.do_select_clicmd)
        self.combobox_cli_command.current(0)
        btn_run_cli_command = tk.Button(frame_bottom, text="Run", command=self.do_cli_run)
        btn_run_cli_command.pack(side="right", fill="x", padx=5, pady=5, expand=False)

        # page for scheduler
        page_sche = tk.Frame(nb)
        #   indicator, enable/disable button
        #   save/load file
        #   the list of scheduler
        lbl_sche_head = tk.Label(page_sche, text="Schedule", font=LARGE_FONT)
        lbl_sche_head.pack(side="top", fill="x", pady=10)

        # page for sensors
        page_sensors = tk.Frame(nb)
        #   the list of sensor status, includes sensor and value
        #   indicator of testmode, no control
        #   indicator, enable/disable auto update
        lbl_sensor_head = tk.Label(page_sensors, text="Sensors", font=LARGE_FONT)
        lbl_sensor_head.pack(side="top", fill="x", pady=10)

        frame_top = tk.Frame(page_sensors)#, background="green")
        frame_bottom = tk.Frame(page_sensors)#, background="yellow")
        frame_top.pack(side="top", fill="both", expand=True)
        frame_bottom.pack(side="bottom", fill="x", expand=False)

        self.mid_query_digitalsensors = -1
        self.buttons_sensors_isactive = False
        self.buttons_sensors_request_full = False # flag to signal the command is finished

        # power DC connection: GetDigitalSensors:SNSR_DC_JACK_CONNECT,0
        devstr = "Power DC Jack"
        self.btn_status_powerdc = guilog.ToggleButton(frame_top, txtt="Connected: "+devstr, txtr="Disconnected: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, state=tk.DISABLED)
        self.btn_status_powerdc.pack(pady=5)

        # Dustbin In: GetDigitalSensors:SNSR_DUSTBIN_IS_IN,1
        devstr = "Dustbin"
        self.btn_status_dustbin = guilog.ToggleButton(frame_top, txtt="In: "+devstr, txtr="Out: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, state=tk.DISABLED)
        self.btn_status_dustbin.pack(pady=5)

        # Left Wheel Extended: GetDigitalSensors:SNSR_LEFT_WHEEL_EXTENDED,0
        devstr = "Left Wheel"
        self.btn_status_leftwheel = guilog.ToggleButton(frame_top, txtt="Extended: "+devstr, txtr="In: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, state=tk.DISABLED)
        self.btn_status_leftwheel.pack(pady=5)

        # Right Wheel Extended: GetDigitalSensors:SNSR_RIGHT_WHEEL_EXTENDED,0
        devstr = "Right Wheel"
        self.btn_status_rightwheel = guilog.ToggleButton(frame_top, txtt="Extended: "+devstr, txtr="In: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, state=tk.DISABLED)
        self.btn_status_rightwheel.pack(pady=5)

        # Left Side Key: GetDigitalSensors:LSIDEBIT,0
        devstr = "Left Side Key"
        self.btn_status_leftsidekey = guilog.ToggleButton(frame_top, txtt="Kicked: "+devstr, txtr="Released: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, state=tk.DISABLED)
        self.btn_status_leftsidekey.pack(pady=5)

        # Left Front Key: GetDigitalSensors:LFRONTBIT,0
        devstr = "Left Front Key"
        self.btn_status_leftfrontkey = guilog.ToggleButton(frame_top, txtt="Kicked: "+devstr, txtr="Released: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, state=tk.DISABLED)
        self.btn_status_leftfrontkey.pack(pady=5)

        # Right Side Key: GetDigitalSensors:RSIDEBIT,0
        devstr = "Right Side Key"
        self.btn_status_rightsidekey = guilog.ToggleButton(frame_top, txtt="Kicked: "+devstr, txtr="Released: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, state=tk.DISABLED)
        self.btn_status_rightsidekey.pack(pady=5)

        # Right Front Key: GetDigitalSensors:RFRONTBIT,0
        devstr = "Right Front Key"
        self.btn_status_rightfrontkey = guilog.ToggleButton(frame_top, txtt="Kicked: "+devstr, txtr="Released: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, state=tk.DISABLED)
        self.btn_status_rightfrontkey.pack(pady=5)

        self.sensors_update_isactive = False
        devstr = "Update Sensors"
        self.btn_sensors_update_enable = guilog.ToggleButton(frame_bottom, txtt="ON: "+devstr, txtr="OFF: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, command=self.guiloop_sensors_update_enable)
        self.btn_sensors_update_enable.pack(pady=5, side="right")

        # page for LiDAR
        page_lidar = tk.Frame(nb)
        #   graph for current data
        #   indicator, enable/disable scanning
        #   buttons to remote control: left/right/up/down/rotate
        lbl_lidar_head = tk.Label(page_lidar, text="LiDAR", font=LARGE_FONT)
        lbl_lidar_head.pack(side="top", fill="x", pady=10)

        frame_top = tk.Frame(page_lidar)#, background="green")
        frame_bottom = tk.Frame(page_lidar)#, background="yellow")
        frame_top.pack(side="top", fill="both", expand=True)
        frame_bottom.pack(side="bottom", fill="x", expand=False)

        self.canvas_lidar = tk.Canvas(frame_top)
        self.canvas_lidar.pack(side="top", fill="both", expand="yes", pady=10)
        self.canvas_lidar_points = {} # 360 items, 0 - 359 degree, lines
        self.canvas_lidar_lines = {}
        self.map_sin_lidar = {}
        self.map_cos_lidar = {}
        for i in range(0,360):
            self.map_cos_lidar[i] = math.cos(CONST_RAD * i) / MAXDIST
            self.map_sin_lidar[i] = math.sin(CONST_RAD * i) / MAXDIST
        self.mid_query_lidar = -1
        self.canvas_lidar_isfocused = False
        self.canvas_lidar_isactive = False
        self.canvas_lidar_request_full = False
        self.state_wheel = STATE_STOP
        self.speed_wheel = 0

        devstr = "LiDAR"
        self.btn_lidar_enable = guilog.ToggleButton(frame_bottom, txtt="ON: "+devstr, txtr="OFF: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, command=self.guiloop_lidar_enable)
        self.btn_lidar_enable.pack(pady=5, side="left")
        self.setup_keypad_navigate(self.canvas_lidar)

        self.wheelctrl_isactive = False
        devstr = "Wheel Controled by Keypad"
        self.btn_wheelctrl_enable = guilog.ToggleButton(frame_bottom, txtt="ON: "+devstr, txtr="OFF: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, command=self.guiloop_wheelctrl_enable)
        self.btn_wheelctrl_enable.pack(pady=5, side="right")

        # page for motors
        page_moto = tk.Frame(nb)
        #   list of motors and each has indicator, start/stop button
        #   warnning message: flip the robot upside down so the wheels are faceing up, before enable wheels moto!
        lbl_moto_head = tk.Label(page_moto, text="Motors", font=LARGE_FONT)
        lbl_moto_head.pack(side="top", fill="x", pady=10)
        s = ttk.Scale(page_moto, orient=tk.HORIZONTAL, length=200, from_=1.0, to=100.0)

        devstr = "Left Wheel"
        self.btn_enable_leftwheel = guilog.ToggleButton(page_moto, txtt="ON: "+devstr, txtr="OFF: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, command=self.guiloop_enable_leftwheel)
        self.btn_enable_leftwheel.pack(pady=5)

        devstr = "Right Wheel"
        self.btn_enable_rightwheel = guilog.ToggleButton(page_moto, txtt="ON: "+devstr, txtr="OFF: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, command=self.guiloop_enable_rightwheel )
        self.btn_enable_rightwheel.pack(pady=5)

        devstr = "LiDAR Motor"
        self.btn_enable_lidarmoto = guilog.ToggleButton(page_moto, txtt="ON: "+devstr, txtr="OFF: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, command=self.guiloop_enable_lidarmoto )
        self.btn_enable_lidarmoto.pack(pady=5)

        devstr = "Vacuum"
        self.btn_enable_vacuum = guilog.ToggleButton(page_moto, txtt="ON: "+devstr, txtr="OFF: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, command=self.guiloop_enable_vacuum )
        self.btn_enable_vacuum.pack(pady=5)

        devstr = "Brush"
        self.btn_enable_brush = guilog.ToggleButton(page_moto, txtt="ON: "+devstr, txtr="OFF: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, command=self.guiloop_enable_brush )
        self.btn_enable_brush.pack(pady=5)

        devstr = "Side Brush"
        self.btn_enable_sidebrush = guilog.ToggleButton(page_moto, txtt="ON: "+devstr, txtr="OFF: "+devstr, imgt=self.img_ledon, imgr=self.img_ledoff, command=self.guiloop_enable_sidebrush )
        self.btn_enable_sidebrush.pack(pady=5)

        # page for Recharge
        page_recharge = tk.Frame(nb)
        # only available when connected to Serial port directly, not for TCP
        lbl_recharge_head = tk.Label(page_recharge, text="Recharge", font=LARGE_FONT)
        lbl_recharge_head.pack(side="top", fill="x", pady=10)

        self.tabtxt_sensors = "Sensors"
        self.tabtxt_lidar = "LiDAR"
        self.tabtxt_status = "Connection"
        nb.add(page_conn, text=self.tabtxt_status)
        nb.add(page_command, text='Commands')
        #nb.add(page_sche, text='Schedule')
        nb.add(page_moto, text='Moto')
        nb.add(page_sensors, text=self.tabtxt_sensors)
        nb.add(page_lidar, text=self.tabtxt_lidar)
        #nb.add(page_recharge, text='Recharge')
        nb.add(page_about, text='About')
        #nb.add(page_testgrid, text='TestGrid')
        #nb.add(page_testpack, text='TestPack')
        nb.bind('<<NotebookTabChanged>>', self.guiloop_nb_tabchanged)

        self.do_cli_disconnect()

    #
    # lidar: support functions
    #
    def guiloop_sensors_update_enable(self):
        b1 = self.btn_sensors_update_enable
        if b1.config('relief')[-1] == 'sunken':
            b1['fg'] = "red"
            self.sensors_update_isactive=True
        else:
            b1['fg'] = "green"
            self.sensors_update_isactive=False
    def guiloop_wheelctrl_enable(self):
        b1 = self.btn_wheelctrl_enable
        if b1.config('relief')[-1] == 'sunken':
            b1['fg'] = "red"
            self.wheelctrl_isactive=True
        else:
            b1['fg'] = "green"
            self.wheelctrl_isactive=False
    def guiloop_lidar_enable(self):
        b1 = self.btn_lidar_enable
        if b1.config('relief')[-1] == 'sunken':
            b1['fg'] = "red"
            self.canvas_lidar_isactive=True
            self.canvas_lidar_isfocused=False
            self._enable_lidar_moto(True)
            self.guiloop_process_lidar(True)
        else:
            b1['fg'] = "green"
            self._enable_lidar_moto(False)
            self.canvas_lidar_isactive=False

    def guiloop_enable_leftwheel(self):
        enable = False
        b1 = self.btn_enable_leftwheel
        if b1.config('relief')[-1] == 'sunken':
            b1['fg'] = "red"
            enable = True
        else:
            b1['fg'] = "green"
        if self.serv_cli != None and self.mid_2b_ignored >= 0:
            self.set_robot_testmode(True)
            if enable:
                self.serv_cli.request(["SetMotor LWheelEnable\nSetMotor LWheelDist 200 Speed 100", self.mid_2b_ignored])
            else:
                self.serv_cli.request(["SetMotor LWheelDisable", self.mid_2b_ignored])

    def guiloop_enable_rightwheel(self):
        enable = False
        b1 = self.btn_enable_rightwheel
        if b1.config('relief')[-1] == 'sunken':
            b1['fg'] = "red"
            enable = True
        else:
            b1['fg'] = "green"
        if self.serv_cli != None and self.mid_2b_ignored >= 0:
            self.set_robot_testmode(True)
            if enable:
                self.serv_cli.request(["SetMotor RWheelEnable\nSetMotor RWheelDist 200 Speed 100", self.mid_2b_ignored])
            else:
                self.serv_cli.request(["SetMotor RWheelDisable", self.mid_2b_ignored])

    def _enable_lidar_moto(self, enable=False):
        if self.serv_cli != None and self.mid_2b_ignored >= 0:
            self.set_robot_testmode(True)
            if enable:
                self.serv_cli.request(["SetLDSRotation On", self.mid_2b_ignored])
            else:
                self.serv_cli.request(["SetLDSRotation Off", self.mid_2b_ignored])
    def guiloop_enable_lidarmoto(self):
        enable = False
        b1 = self.btn_enable_lidarmoto
        if b1.config('relief')[-1] == 'sunken':
            b1['fg'] = "red"
            enable = True
        else:
            b1['fg'] = "green"
        self._enable_lidar_moto(enable)

    def guiloop_enable_vacuum(self):
        enable = False
        b1 = self.btn_enable_vacuum
        if b1.config('relief')[-1] == 'sunken':
            b1['fg'] = "red"
            enable = True
        else:
            b1['fg'] = "green"
        if self.serv_cli != None and self.mid_2b_ignored >= 0:
            self.set_robot_testmode(True)
            if enable:
                self.serv_cli.request(["SetMotor VacuumOn", self.mid_2b_ignored])
            else:
                self.serv_cli.request(["SetMotor VacuumOff", self.mid_2b_ignored])

    def guiloop_enable_brush(self):
        enable = False
        b1 = self.btn_enable_brush
        if b1.config('relief')[-1] == 'sunken':
            b1['fg'] = "red"
            enable = True
        else:
            b1['fg'] = "green"
        if self.serv_cli != None and self.mid_2b_ignored >= 0:
            self.set_robot_testmode(True)
            if enable:
                self.serv_cli.request(["SetMotor BrushEnable\nSetMotor Brush RPM 250", self.mid_2b_ignored])
            else:
                self.serv_cli.request(["SetMotor BrushDisable", self.mid_2b_ignored])

    def guiloop_enable_sidebrush(self):
        enable = False
        b1 = self.btn_enable_sidebrush
        if b1.config('relief')[-1] == 'sunken':
            b1['fg'] = "red"
            enable = True
        else:
            b1['fg'] = "green"
        if self.serv_cli != None and self.mid_2b_ignored >= 0:
            self.set_robot_testmode(True)
            if enable:
                self.serv_cli.request(["SetMotor BrushEnable\nSetMotor Brush RPM 250", self.mid_2b_ignored])
            else:
                self.serv_cli.request(["SetMotor BrushDisable", self.mid_2b_ignored])

    # called by GUI when the tab is changed
    def guiloop_nb_tabchanged(self, event):
        # check if the LiDAR tab is open
        cur_focus = False
        if event.widget.tab(event.widget.index("current"),"text") == self.tabtxt_lidar:
            cur_focus = True
            self.canvas_lidar.focus_set() # when switch to the lidar page, use the canvas as the front widget to receive key events!
        self.guiloop_process_lidar(cur_focus)

        # check if the Sensors tab is open
        cur_focus = False
        if event.widget.tab(event.widget.index("current"),"text") == self.tabtxt_sensors:
            cur_focus = True
        self.guiloop_process_sensors(cur_focus)

        # check if the Status tab is open
        cur_focus = False
        if event.widget.tab(event.widget.index("current"),"text") == self.tabtxt_status:
            cur_focus = True
        self.guiloop_process_status(cur_focus)

    # called by GUI when the tab is changed to status
    def guiloop_process_status(self, cur_focus):
        L.info('switched to tab status: previous=' + str(self.status_isactive) + ", current=" + str(cur_focus))
        self.status_isactive = cur_focus
        #self.status_request()

    # called by GUI when the tab is changed to sensors
    def guiloop_process_sensors(self, cur_focus):
        L.info('switched to tab sensor: previous=' + str(self.buttons_sensors_isactive) + ", current=" + str(cur_focus))
        self.buttons_sensors_isactive = cur_focus
        self.buttons_sensors_request()

    # the state machine for controling the wheel's movement
    def smachine_wheelctrl(self, key):
        #try:
        #    {
        #        STATE_STOP:    case_wheelctrl_ststop,
        #        STATE_FORWARD: case_wheelctrl_stforword,
        #        STATE_BACK:    case_wheelctrl_stback,
        #        STATE_LEFT:    case_wheelctrl_stleft,
        #        STATE_RIGHT:   case_wheelctrl_stright,
        #    }[self.state_wheel](key)
        #except KeyError:
        #    # default action
        #    L.error("no such state: " + str(self.state_wheel))
        if key == KEY_UP:
            if self.state_wheel == STATE_BACK:
                self.state_wheel = STATE_STOP
                if self.serv_cli != None and self.mid_2b_ignored >= 0:
                    self.set_robot_testmode(True)
                    self.serv_cli.request(["SetMotor LWheelDisable RWheelDisable", self.mid_2b_ignored])
                    #self.serv_cli.request(["SetMotor RWheelEnable LWheelEnable\nSetMotor LWheelDist 2500 RWheelDist -2500 Speed 100", self.mid_2b_ignored])
            elif self.state_wheel == STATE_FORWARD:
                if self.speed_wheel < 300:
                    self.speed_wheel += 50
                if self.serv_cli != None and self.mid_2b_ignored >= 0:
                    self.set_robot_testmode(True)
                    self.serv_cli.request(["SetMotor LWheelDist 5000 RWheelDist 5000 Speed " + str(self.speed_wheel), self.mid_2b_ignored])
            else:
                self.state_wheel = STATE_FORWARD
                self.speed_wheel = 50
                if self.serv_cli != None and self.mid_2b_ignored >= 0:
                    self.set_robot_testmode(True)
                    self.serv_cli.request(["SetMotor RWheelEnable LWheelEnable\nSetMotor LWheelDist 5000 RWheelDist 5000 Speed " + str(self.speed_wheel), self.mid_2b_ignored])
        elif key == KEY_DOWN:
            if self.state_wheel == STATE_STOP:
                self.state_wheel = STATE_BACK
                if self.serv_cli != None and self.mid_2b_ignored >= 0:
                    self.set_robot_testmode(True)
                    self.serv_cli.request(["SetMotor RWheelEnable LWheelEnable\nSetMotor LWheelDist -5000 RWheelDist -5000 Speed 100", self.mid_2b_ignored])
            else:
                self.state_wheel = STATE_STOP
                if self.serv_cli != None and self.mid_2b_ignored >= 0:
                    self.set_robot_testmode(True)
                    self.serv_cli.request(["SetMotor LWheelDisable RWheelDisable", self.mid_2b_ignored])
        elif key == KEY_LEFT:
            if self.state_wheel == STATE_RIGHT:
                self.state_wheel = STATE_STOP
                if self.serv_cli != None and self.mid_2b_ignored >= 0:
                    self.set_robot_testmode(True)
                    self.serv_cli.request(["SetMotor LWheelDisable RWheelDisable", self.mid_2b_ignored])
            else:
                self.state_wheel = STATE_LEFT
                if self.serv_cli != None and self.mid_2b_ignored >= 0:
                    self.set_robot_testmode(True)
                    self.serv_cli.request(["SetMotor RWheelEnable LWheelEnable\nSetMotor LWheelDist -2500 RWheelDist 2500 Speed 100", self.mid_2b_ignored])
        elif key == KEY_RIGHT:
            if self.state_wheel == STATE_LEFT:
                self.state_wheel = STATE_STOP
                if self.serv_cli != None and self.mid_2b_ignored >= 0:
                    self.set_robot_testmode(True)
                    self.serv_cli.request(["SetMotor LWheelDisable RWheelDisable", self.mid_2b_ignored])
            else:
                self.state_wheel = STATE_RIGHT
                if self.serv_cli != None and self.mid_2b_ignored >= 0:
                    self.set_robot_testmode(True)
                    self.serv_cli.request(["SetMotor RWheelEnable LWheelEnable\nSetMotor LWheelDist 2500 RWheelDist -2500 Speed 100", self.mid_2b_ignored])
        elif key == KEY_BACK:
            self.state_wheel = STATE_STOP
            if self.serv_cli != None and self.mid_2b_ignored >= 0:
                self.set_robot_testmode(True)
                self.serv_cli.request(["SetMotor LWheelDisable RWheelDisable", self.mid_2b_ignored])

    # keypad for navigation
    #def keyup_navigate(self, event):
    #    L.info('key up' + event.char)
    def keydown_navigate(self, event):
        if self.wheelctrl_isactive == False:
            return
        #L.info('key down ' + event.char)
        # WSAD
        key = KEY_NONE
        if event.keysym == 'Right':
            L.info('key down: Arrow Right')
            key = KEY_RIGHT
            pass
        elif event.keysym == 'Left':
            L.info('key down: Arrow Left')
            key = KEY_LEFT
            pass
        elif event.keysym == 'Up':
            L.info('key down: Arrow Up')
            key = KEY_UP
            pass
        elif event.keysym == 'Down':
            L.info('key down: Arrow Down')
            key = KEY_DOWN
            pass
        elif event.keysym == 'space' or event.keysym == 'BackSpace' or event.keysym == 'Escape':
            L.info('key down: Esc')
            key = KEY_BACK
            pass
        elif event.char == 'w' or event.char == 'W':
            L.info('key: w')
            key = KEY_UP
            pass
        elif event.char == 's' or event.char == 'S':
            L.info('key: s')
            key = KEY_DOWN
            pass
        elif event.char == 'a' or event.char == 'A':
            L.info('key: a')
            key = KEY_LEFT
            pass
        elif event.char == 'd' or event.char == 'D':
            L.info('key: d')
            key = KEY_RIGHT
            pass
        else:
            L.info('other key down: ' + event.char)
        self.smachine_wheelctrl(key)

    def setup_keypad_navigate(self, widget):
        #widget.bind("<KeyRelease>", self.keyup_navigate)
        widget.bind("<KeyPress>", self.keydown_navigate)

    # called by GUI when the tab is changed to lidar
    def guiloop_process_lidar(self, cur_focus):
        if self.canvas_lidar_isactive == False:
            self.canvas_lidar_isfocused = cur_focus
            return
        if self.canvas_lidar_isfocused == False:
            if cur_focus == True:
                self.canvas_lidar_isfocused = cur_focus
                self._canvas_lidar_process_focus()
        else:
            if cur_focus == False:
                self.canvas_lidar_isfocused = cur_focus
                self._canvas_lidar_process_focus()

    # the periodical routine for the widgets of Sensors
    def buttons_sensors_request(self):
        if self.buttons_sensors_isactive:
            if self.serv_cli != None:
                if self.mid_query_digitalsensors < 0 :
                    L.info('create mid_query_digitalsensors')
                    self.mid_query_digitalsensors = self.serv_cli.mailbox.declair()
                if self.mid_query_digitalsensors >= 0 and self.buttons_sensors_request_full == False and self.sensors_update_isactive:
                    L.info('Request GetDigitalSensors ...')
                    self.buttons_sensors_request_full = True
                    self.serv_cli.request(["GetDigitalSensors\n", self.mid_query_digitalsensors])
            #L.info('setup next call buttons_sensors_request ...')
            self.after(500, self.buttons_sensors_request)

    # the periodical routine for the widgets of LiDAR
    def canvas_lidar_request(self):
        if self.serv_cli != None and self.mid_query_lidar >= 0:
            if self.canvas_lidar_isfocused and self.canvas_lidar_request_full == False:
                self.serv_cli.request(["GetLDSScan\n", self.mid_query_lidar])
                self.canvas_lidar_request_full = True

        if self.canvas_lidar_isfocused and self.canvas_lidar_isactive:
            self.after(300, self.canvas_lidar_request)

    def _canvas_lidar_process_focus(self):
        if self.canvas_lidar_isfocused == True:
            self.set_robot_testmode(True)
            if self.serv_cli != None:
                if self.mid_query_lidar < 0 :
                    L.info('LiDAR canvas focus <---')
                    self.mid_query_lidar = self.serv_cli.mailbox.declair()
                self.canvas_lidar_request()
        #else:
            #self.canvas_lidar_isactive = False
            #self.serv_cli.mailbox.close(self.mid_query_lidar)

    def mailpipe_process_digitalsensors(self):
        if self.serv_cli != None and self.mid_query_digitalsensors >= 0:
            try:
                pre=None
                while True:
                    # remove all of items in the queue
                    try:
                        respstr = self.serv_cli.mailbox.get(self.mid_query_digitalsensors, False)
                        if respstr == None:
                            break
                        L.info('digital sensors data pulled out!')
                        pre = respstr
                    except queue.Empty:
                        # ignore
                        break
                respstr = pre
                if respstr == None:
                    return
                retlines = respstr.strip() + '\n'
                responses = retlines.split('\n')
                for i in range(0,len(responses)):
                    response = responses[i].strip()
                    if len(response) < 1:
                        break
                    lst = response.split(',')
                    if len(lst) < 2:
                        continue
                    label = lst[0].strip().lower()
                    if label == 'SNSR_DC_JACK_CONNECT'.lower():
                        # do power dc jack ...
                        if lst[1].strip() == "1":
                            self.btn_status_powerdc.config(relief='sunken')
                        else:
                            self.btn_status_powerdc.config(relief='raised')
                    elif label == 'SNSR_DUSTBIN_IS_IN'.lower():
                        # do dustbin ...
                        if lst[1].strip() == "1":
                            self.btn_status_dustbin.config(relief='sunken')
                        else:
                            self.btn_status_dustbin.config(relief='raised')
                    elif label == 'SNSR_LEFT_WHEEL_EXTENDED'.lower():
                        if lst[1].strip() == "1":
                            self.btn_status_leftwheel.config(relief='sunken')
                        else:
                            self.btn_status_leftwheel.config(relief='raised')
                    elif label == 'SNSR_RIGHT_WHEEL_EXTENDED'.lower():
                        if lst[1].strip() == "1":
                            self.btn_status_rightwheel.config(relief='sunken')
                        else:
                            self.btn_status_rightwheel.config(relief='raised')
                    elif label == 'LSIDEBIT'.lower():
                        if lst[1].strip() == "1":
                            self.btn_status_leftsidekey.config(relief='sunken')
                        else:
                            self.btn_status_leftsidekey.config(relief='raised')
                    elif label == 'LFRONTBIT'.lower():
                        if lst[1].strip() == "1":
                            self.btn_status_leftfrontkey.config(relief='sunken')
                        else:
                            self.btn_status_leftfrontkey.config(relief='raised')
                    elif label == 'RSIDEBIT'.lower():
                        if lst[1].strip() == "1":
                            self.btn_status_rightsidekey.config(relief='sunken')
                        else:
                            self.btn_status_rightsidekey.config(relief='raised')
                    elif label == 'RFRONTBIT'.lower():
                        if lst[1].strip() == "1":
                            self.btn_status_rightfrontkey.config(relief='sunken')
                        else:
                            self.btn_status_rightfrontkey.config(relief='raised')

                L.info('digital sensors updated!')
            except queue.Empty:
                # ignore
                pass
            self.buttons_sensors_request_full = False

    def mailpipe_process_lidar(self):
        if self.serv_cli != None and self.mid_query_lidar >= 0:
            try:
                pre=None
                while True:
                    # remove all of items in the queue
                    try:
                        respstr = self.serv_cli.mailbox.get(self.mid_query_lidar, False)
                        if respstr == None:
                            break
                        L.info('LiDAR data pulled out!')
                        pre = respstr
                    except queue.Empty:
                        # ignore
                        break
                respstr = pre
                if respstr == None:
                    return
                width = self.canvas_lidar.winfo_width()
                height = self.canvas_lidar.winfo_height()
                MAXCOOD = height
                if width < height:
                    MAXCOOD = width
                MAXCOOD = int(MAXCOOD / 2)
                MAXCOODX = int(width / 2)
                MAXCOODY = int(height / 2)
                CIRRAD=2
                if 1 == 1:
                    #self.canvas_lidar.xview_scroll(width, "units")
                    #self.canvas_lidar.yview_scroll(height, "units")
                    self.canvas_lidar.configure(scrollregion=(0-MAXCOODX, 0-MAXCOODY, MAXCOODX, MAXCOODY))
                    MAXCOODX = 0
                    MAXCOODY = 0
                #L.info('LiDAR canvas sz=(' + str(width) + ", " + str(height) + "), maxcood=(" + str(MAXCOODX) + ", " + str(MAXCOODY) + ") " + str(MAXCOOD))

                retlines = respstr.strip() + '\n'
                responses = retlines.split('\n')
                for i in range(0,len(responses)):
                    response = responses[i].strip()
                    if len(response) < 1:
                        break
                    lst = response.split(',')
                    if len(lst) < 4:
                        continue
                    if lst[0].lower() == 'AngleInDegrees'.lower():
                        continue
                    angle = int(lst[0])
                    if angle < 0 or angle > 359:
                        continue
                    distmm = int(lst[1])
                    intensity = int(lst[2])
                    #errval = lst[3]
                    #if distmm > 1600:
                    #    distmm = MAXDIST
                    #if errval != "0":
                    #    distmm = MAXDIST
                    #L.info('LiDAR angle=' + str(angle) + ", dist=" + str(distmm) + ", intensity=" + str(intensity) )

                    if distmm == 0:
                        posx = MAXCOODX
                        posy = MAXCOODY
                    else:
                        off = distmm * MAXCOOD
                        posx = MAXCOODX + off * self.map_cos_lidar[angle]
                        posy = MAXCOODY + off * self.map_sin_lidar[angle]
                    #L.info('LiDAR angle=' + str(angle) + ", pos=(" + str(posx) + "," + str(posy) +")" )

                    #save to the list
                    if angle in self.canvas_lidar_lines:
                        # update
                        i = self.canvas_lidar_lines[angle]
                        self.canvas_lidar.coords(i, MAXCOODX, MAXCOODY, posx, posy)
                    else:
                        # create a new line
                        i = self.canvas_lidar.create_line(MAXCOODX, MAXCOODY, posx, posy, fill="red", dash=(4, 4))
                        self.canvas_lidar_lines[angle] = i

                    if angle in self.canvas_lidar_points:
                        # update
                        i = self.canvas_lidar_points[angle]
                        self.canvas_lidar.coords(i, posx - CIRRAD, posy - CIRRAD, posx + CIRRAD, posy + CIRRAD)
                    else:
                        # create a new line
                        i = self.canvas_lidar.create_oval(posx - CIRRAD, posy - CIRRAD, posx + CIRRAD, posy + CIRRAD, outline="green", fill="green", width=1)
                        #i = self.canvas_lidar.create_circle(posx, posy, CIRRAD, outline="green", fill="green", width=1)
                        self.canvas_lidar_points[angle] = i

                L.info('LiDAR canvas updated!')
            except queue.Empty:
                # ignore
                pass
            self.canvas_lidar_request_full = False

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
        self.serv_cli = neatocmdapi.NCIService(target=self.client_port.get().strip(), timeout=2)
        if self.serv_cli.open(self.cb_task_cli) == False:
            L.error ('Error in open serial')
            return
        L.info ('serial opened')

        self.mid_2b_ignored = self.serv_cli.mailbox.declair()  # the index of the return data Queue for any command that don't need to be parsed the data
        self.mid_cli_command = self.serv_cli.mailbox.declair() # the index of the return data Queue for 'Commands' tab
        self.mid_query_version = self.serv_cli.mailbox.declair() # the index of the return data Queue for version textarea
        self.mid_query_time = self.serv_cli.mailbox.declair()    # the index of the return data Queue for robot time label
        self.mid_query_battery = self.serv_cli.mailbox.declair() # the index of the return data Queue for robot battery % ratio

        self.serv_cli.request(["GetVersion", self.mid_query_version])
        self.serv_cli.request(["GetWarranty", self.mid_query_version])
        self.guiloop_check_rightnow()
        self.guiloop_check_per1sec()
        self.guiloop_check_per30sec()
        self.btn_cli_connect.config(state=tk.DISABLED)
        self.btn_cli_disconnect.config(state=tk.NORMAL)
        return

    def do_cli_disconnect(self):
        import time
        if self.serv_cli != None:
            L.info('client disconnect ...')
            self.set_robot_testmode(False)
            time.sleep(1)
            self.serv_cli.close()
        else:
            L.info('client is not connected, skip.')
        self.serv_cli = None
        self.mid_2b_ignored = -1
        self.mid_cli_command = -1
        self.mid_query_version = -1
        self.mid_query_time = -1
        self.mid_query_battery = -1
        self.mid_query_lidar = -1
        self.mid_query_digitalsensors = -1

        self.buttons_sensors_request_full = False # flag to signal the command is finished
        self.canvas_lidar_request_full = False

        self.btn_cli_connect.config(state=tk.NORMAL)
        self.btn_cli_disconnect.config(state=tk.DISABLED)

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

    def mailpipe_process_conn_cmd(self):

        if self.mid_2b_ignored >= 0:
            try:
                while True:
                    # remove all of items in the queue
                    try:
                        respstr = self.serv_cli.mailbox.get(self.mid_2b_ignored, False)
                        if respstr == None:
                            break
                        L.info('ignore the response: ' + respstr)
                    except queue.Empty:
                        break
            except queue.Empty:
                # ignore
                pass

        if self.mid_cli_command >= 0:
            try:
                resp = self.serv_cli.mailbox.get(self.mid_cli_command, False)
                respstr = resp.strip() + "\n\n"
                # put the content to the end of the textarea
                guilog.textarea_append (self.text_cli_command, respstr)
                self.text_cli_command.update_idletasks()
            except queue.Empty:
                # ignore
                pass

        if self.mid_query_version >= 0:
            try:
                resp = self.serv_cli.mailbox.get(self.mid_query_version, False)
                respstr = resp.strip()
                self.show_robot_version (respstr)
            except queue.Empty:
                # ignore
                pass

        if self.mid_query_battery >= 0:
            try:
                while True:
                    respstr = self.serv_cli.mailbox.get(self.mid_query_battery, False)
                    if respstr == None:
                        break
                    retlines = respstr.strip() + '\n'
                    responses = retlines.split('\n')
                    for i in range(0,len(responses)):
                        response = responses[i].strip()
                        if len(response) < 1:
                            #L.debug('read null 2')
                            break
                        lst = response.split(',')
                        if len(lst) > 1:
                            if lst[0].lower() == 'FuelPercent'.lower():
                                L.debug('got fule percent: ' + lst[1])
                                self.show_battery_level(int(lst[1]))
            except queue.Empty:
                # ignore
                pass

        if self.mid_query_time >= 0:
            import re
            try:
                while True:
                    respstr = self.serv_cli.mailbox.get(self.mid_query_time, False)
                    if respstr == None:
                        break
                    retlines = respstr.strip()
                    retlines = respstr.strip() + '\n'
                    responses = retlines.split('\n')
                    for i in range(0,len(responses)):
                        response = responses[i].strip()
                        if len(response) < 1:
                            #L.debug('read null 2')
                            break
                        lst1 = response.split(' ')
                        if lst1[0] in {'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',}:
                            L.debug("gettime: " + response)
                            self.show_robot_time(response)
            except queue.Empty:
                # ignore
                pass

    def guiloop_check_rightnow(self):
        if self.serv_cli != None:
            self.mailpipe_process_conn_cmd()
            self.mailpipe_process_lidar()
            self.mailpipe_process_digitalsensors()
            # setup next
            self.after(100, self.guiloop_check_rightnow)
        return

    def guiloop_check_per1sec(self):
        if self.serv_cli != None:
            # setup next
            if self.status_isactive == True:
                self.serv_cli.request(["GetTime", self.mid_query_time]) # query the time
            self.after(5000, self.guiloop_check_per1sec)
        return

    def guiloop_check_per30sec(self):
        if self.serv_cli != None:
            # setup next
            if self.status_isactive == True:
                self.serv_cli.request(["GetCharger", self.mid_query_battery]) # query the level of battery
            self.after(30000, self.guiloop_check_per30sec)
        return

    def set_robot_time_from_pc(self):
        if self.serv_cli == None:
            L.error('client is not connected, please connect it first!')
            return
        import time
        tm_now = time.localtime()
        cmdstr = time.strftime("SetTime Day %w Hour %H Min %M Sec %S", tm_now)
        self.serv_cli.request([cmdstr, self.mid_2b_ignored])

    def set_robot_testmode (self, istest = False):
        L.info('call set_robot_testmode("' + str(istest) + '")!')
        if self.istestmode != istest:
            if self.serv_cli != None and self.mid_2b_ignored >= 0:
                if istest:
                    self.serv_cli.request(["TestMode On", self.mid_2b_ignored])
                else:
                    self.serv_cli.request(["SetLDSRotation Off\nSetMotor LWheelDisable RWheelDisable BrushDisable VacuumOff\nTestMode Off", self.mid_2b_ignored])
        self.istestmode = istest
        self.show_robot_testmode(istest)

def neatosetup_main():
    guilog.set_log_stderr()

    root = tk.Tk()
    root.title(str_progname + " - " + str_version)

    #nb.pack(expand=1, fill="both")
    MyTkAppFrame(root).pack(fill="both", expand=True)
    #ttk.Sizegrip(root).grid(column=999, row=999, sticky=(tk.S,tk.E))
    ttk.Sizegrip(root).pack(side="right")
    root.mainloop()

if __name__ == "__main__":
    neatosetup_main()



