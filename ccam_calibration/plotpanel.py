import tkinter as tk
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.figure import Figure
import os
from ccam_calibration.radianceCalibration import RadianceCalibration


class PlotPanel(tk.Frame):

    def __init__(self, window, *args, **kwargs):
        """
        Initialize the GUI and its components
        """
        self.window = window
        tk.Frame.__init__(self, window, *args, **kwargs)

        # set row/column growth for grid layout
        tk.Grid.rowconfigure(window, 1, weight=3)
        tk.Grid.columnconfigure(window, 2, weight=3)

        self.filename_dict = {}

        self.frame = tk.Frame(self.window)
        self.file_list_label = tk.Label(self.window, text="Files: ")
        self.vscrollbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL)
        self.hscrollbar = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL)
        self.file_list_box = tk.Listbox(self.frame, selectmode="extended", width=40,  yscrollcommand=self.vscrollbar.set, xscrollcommand=self.hscrollbar.set)
        self.vscrollbar.config(command=self.file_list_box.yview)
        self.hscrollbar.config(command=self.file_list_box.xview)
        self.add_file_button = tk.Button(self.window, text="Add", command=self.add_file)
        self.rm_file_button = tk.Button(self.window, text="Remove", command=self.remove_file)
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.axes = self.fig.add_subplot(111)
        self.export_button = tk.Button(self.window, text="Save Plot", command=self.save_plot)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)

        # read wavelengths for x-axis of plots
        my_path = os.path.abspath(os.path.dirname(__file__))
        gain_file = os.path.join(my_path, "constants/gain_mars.edit")
        (self.wavelength, gain) = RadianceCalibration.get_wl_and_gain(gain_file)

        self.set_up_layout()

    def set_up_layout(self):
        """
        set up the GUI layout
        :return: None
        """
        self.vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.file_list_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.file_list_label.grid(row=0, column=0, columnspan=2, padx=(10, 10))
        self.frame.grid(row=1, column=0, columnspan=2, padx=(10, 10), sticky="ewns")
        self.add_file_button.grid(row=2, column=0, padx=(10, 0), pady=(10, 10), sticky="ew")
        self.rm_file_button.grid(row=2, column=1, padx=(0, 10), pady=(10, 10), sticky="ew")
        self.canvas.get_tk_widget().grid(row=0, column=2, rowspan=2)
        self.export_button.grid(row=2, column=2, sticky="ew", pady=(10, 10))

    @staticmethod
    def read_file(file):
        data = []
        if "tab" in file:
            if "rad" in file:
                with open(file) as f:
                    data = [float(x.split()[1].strip()) for index, x in enumerate(f) if index > 28]
            elif "ref" in file:
                data = [float(x.split()[1].strip()) for x in open(file).readlines()]
            # elif "psv" in file:
            #     with open(file) as f:
            #         data = [float(x.strip()) for index, x in enumerate(f) if index > 28]
        return data

    def add_file(self):
        """add_file
        """
        # open file chooser, select file
        files = tk.filedialog.askopenfilenames()

        # add file to list
        list_of_files = self.window.tk.splitlist(files)

        for file in list_of_files:
            (path, filename) = os.path.split(file)
            self.filename_dict[filename] = path
            self.file_list_box.insert(tk.END, filename)

            # add file to graph
            # Data for plotting
            data = self.read_file(file)
            if len(data) == len(self.wavelength):
                self.axes.plot(self.wavelength, data, label=filename)
                self.axes.legend()
                self.canvas.draw()

    def remove_file(self):
        """remove_file
        """
        # remove the highlighted files from list and graph
        self.file_list_box.delete(tk.ACTIVE)

    def save_plot(self):
        # TODO save plot
        print("save plot")

    def _quit(self):
        self.window.quit()     # stops mainloop
        self.window.destroy()  # this is necessary on Windows to prevent
                               # Fatal Python Error: PyEval_RestoreThread: NULL tstate

