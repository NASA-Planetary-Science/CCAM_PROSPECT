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

        self.file_box_frame = tk.Frame(self.window)
        self.axis_adjust_frame = tk.Frame(self.window)

        self.file_list_label = tk.Label(self.window, text="Files: ")
        self.vscrollbar = tk.Scrollbar(self.file_box_frame, orient=tk.VERTICAL)
        self.hscrollbar = tk.Scrollbar(self.file_box_frame, orient=tk.HORIZONTAL)
        self.file_list_box = tk.Listbox(self.file_box_frame, selectmode="extended", width=40, yscrollcommand=self.vscrollbar.set, xscrollcommand=self.hscrollbar.set)
        self.vscrollbar.config(command=self.file_list_box.yview)
        self.hscrollbar.config(command=self.file_list_box.xview)
        self.add_file_button = tk.Button(self.window, text="Add", command=self.add_file)
        self.rm_file_button = tk.Button(self.window, text="Remove", command=self.remove_file)
        self.fig = Figure(figsize=(7, 4), dpi=100)
        self.axes = self.fig.add_subplot(111)
        self.export_button = tk.Button(self.window, text="Save Plot", command=self.save_plot)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        self.axes.set_ylabel('Relative Reflectance')
        self.axes.set_xlabel('Wavelength (nm)')
        self.y_axis_min_label = tk.Label(self.axis_adjust_frame, text="min: ")
        self.y_axis_max_label = tk.Label(self.axis_adjust_frame, text="max: ")
        self.y_axis_min_entry = tk.Entry(self.axis_adjust_frame, width=10)
        self.y_axis_max_entry = tk.Entry(self.axis_adjust_frame, width=10)
        self.y_axis_label = tk.Label(self.axis_adjust_frame, text="Y-Axis")
        self.x_axis_min_label = tk.Label(self.axis_adjust_frame, text="min: ")
        self.x_axis_max_label = tk.Label(self.axis_adjust_frame, text="max: ")
        self.x_axis_min_entry = tk.Entry(self.axis_adjust_frame, width=10)
        self.x_axis_max_entry = tk.Entry(self.axis_adjust_frame, width=10)
        self.x_axis_label = tk.Label(self.axis_adjust_frame, text="X-Axis")
        self.axis_apply = tk.Button(self.axis_adjust_frame, text="Apply", command=self.apply_axis)

        self.y_axis_min_entry.insert(tk.END, "0")
        self.y_axis_max_entry.insert(tk.END, "1")
        self.x_axis_min_entry.insert(tk.END, "400")
        self.x_axis_max_entry.insert(tk.END, "840")

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
        self.file_box_frame.grid(row=1, column=0, columnspan=2, padx=(10, 10), sticky="ewns")
        self.add_file_button.grid(row=2, column=0, padx=(10, 0), pady=(10, 10), sticky="ew")
        self.rm_file_button.grid(row=2, column=1, padx=(0, 10), pady=(10, 10), sticky="ew")
        self.canvas.get_tk_widget().grid(row=0, column=2, rowspan=4)
        self.export_button.grid(row=4, column=2, sticky="ew", pady=(10, 10))
        self.y_axis_label.grid(row=0, column=0, columnspan=2)
        self.y_axis_min_label.grid(row=1, column=0)
        self.y_axis_min_entry.grid(row=1, column=1, padx=(0, 10))
        self.y_axis_max_label.grid(row=2, column=0)
        self.y_axis_max_entry.grid(row=2, column=1, padx=(0, 10))
        self.x_axis_label.grid(row=3, column=0, columnspan=2)
        self.x_axis_min_label.grid(row=4, column=0)
        self.x_axis_min_entry.grid(row=4, column=1, padx=(0, 10))
        self.x_axis_max_label.grid(row=5, column=0)
        self.x_axis_max_entry.grid(row=5, column=1, padx=(0, 10))
        self.axis_apply.grid(row=6, column=0, columnspan=2, sticky="ew")
        self.axis_adjust_frame.grid(row=1, column=3)

    @staticmethod
    def read_file(file):
        x = []
        y = []
        with open(file) as f:
            data = [x for index, x in enumerate(f) if 2428 < index < 4039 or 4112 < index < 5810]
            x = [float(line.split()[0].strip()) for line in data]
            y = [float(line.split()[1].strip()) for line in data]

        return x, y

    def add_file(self):
        """add_file
        """
        # open file chooser, select file
        files = tk.filedialog.askopenfilenames()

        # add file to list
        list_of_files = self.window.tk.splitlist(files)

        for file in list_of_files:
            if "tab" in file and "ref" in file:
                (path, filename) = os.path.split(file)
                self.filename_dict[filename] = path
                self.file_list_box.insert(tk.END, filename)

                # add file to graph
                # Data for plotting
                x, y = self.read_file(file)
                self.axes.plot(x, y, label=filename)
                self.axes.legend(bbox_to_anchor=(0.4, 0.5), loc='lower left', borderaxespad=0.)
                self.canvas.draw()

    def remove_file(self):
        """remove_file
        """
        # remove the highlighted files from list and graph
        self.file_list_box.delete(tk.ACTIVE)

    def save_plot(self):
        # TODO save plot
        print("save plot")

    def apply_axis(self):
        xmin = float(self.x_axis_min_entry.get())
        xmax = float(self.x_axis_max_entry.get())
        ymin = float(self.y_axis_min_entry.get())
        ymax = float(self.y_axis_max_entry.get())

        self.axes.set_xlim(xmin, xmax)
        self.axes.set_ylim(ymin, ymax)
        self.canvas.draw()

    def _quit(self):
        self.window.quit()     # stops mainloop
        self.window.destroy()  # this is necessary on Windows to prevent
                               # Fatal Python Error: PyEval_RestoreThread: NULL tstate
