import tkinter as tk
from tkinter import filedialog, ttk, messagebox, Grid, END, ACTIVE
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import numpy as np
import os
from ccam_calibration.radianceCalibration import RadianceCalibration


class PlotPanel(tk.Frame):

    def __init__(self, window, *args, **kwargs):
        """
        Initialize the GUI and its components
        """
        self.window = window
        tk.Frame.__init__(self, window, *args, **kwargs)

        Grid.columnconfigure(window, 2, weight=3)

        self.file_list_label = tk.Label(self.window, text="Files: ")
        self.file_list_box = tk.Listbox(self.window, selectmode="multiple")
        self.add_file_button = tk.Button(self.window, text="Add", command=self.add_file)
        self.rm_file_button = tk.Button(self.window, text="Remove", command=self.remove_file)
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)

        # read wavelength for x-axis of plots
        my_path = os.path.abspath(os.path.dirname(__file__))
        gain_file = os.path.join(my_path, "constants/gain_mars.edit")
        (self.wavelength, gain) = RadianceCalibration.get_wl_and_gain(gain_file)

        self.set_up_layout()

    def set_up_layout(self):
        """
        set up the GUI layout
        :return: None
        """
        self.file_list_label.grid(row=0, column=0, columnspan=2)
        self.file_list_box.grid(row=1, column=0, columnspan=2)
        self.add_file_button.grid(row=2, column=0)
        self.rm_file_button.grid(row=2, column=1)
        self.canvas.get_tk_widget().grid(row=1, column=2, rowspan=2)

    @staticmethod
    def read_file(file):
        if "rad" in file:
            with open(file) as f:
                data = [float(x.split()[1].strip()) for index, x in enumerate(f) if index > 28]
        elif "ref" in file:
            data = [float(x.split()[1].strip()) for x in open(file).readlines()]
        # elif "psv" in file:
        #     with open(file) as f:
        #         data = [float(x.strip()) for index, x in enumerate(f) if index > 28]
        else:
            # not a valid file name - throw an error and remove from list
            data = []
        return data

    def add_file(self):
        """add_file
        """
        # open file chooser, select file
        file = filedialog.askopenfilename()

        # add file to list
        self.file_list_box.insert(END, file)

        # add file to graph
        # Data for plotting
        data = self.read_file(file)
        if len(data) == len(self.wavelength):
            self.fig.add_subplot(111).plot(self.wavelength, data)
            self.canvas.draw()

    def remove_file(self):
        """remove_file
        """
        # remove the highlighthed files from list and graph
        self.file_list_box.delete(ACTIVE)

    def _quit(self):
        self.window.quit()     # stops mainloop
        self.window.destroy()  # this is necessary on Windows to prevent
                               # Fatal Python Error: PyEval_RestoreThread: NULL tstate

