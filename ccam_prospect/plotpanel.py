import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# Implement the default Matplotlib key bindings.
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import os


class PlotPanel(tk.Frame):

    def __init__(self, window, btn, *args, **kwargs):
        """
        Initialize the GUI and its components
        """
        self.window = window
        self.close_button = btn
        tk.Frame.__init__(self, window, *args, **kwargs)

        # set row/column growth for grid layout
        tk.Grid.rowconfigure(window, 1, weight=3)
        tk.Grid.columnconfigure(window, 2, weight=3)

        self.filename_dict = {}
        self.lines_dict = {}

        self.file_box_frame = tk.Frame(self.window)
        self.axis_adjust_frame = tk.Frame(self.window)

        self.back_to_main = tk.Button(self.window, text="<< Back to Calibration", command=self.back_button_pressed)
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
        self.axes.set_xlim(400, 840)

        self.set_up_layout()

    def set_up_layout(self):
        """
        set up the GUI layout
        :return: None
        """
        # self.back_to_main.grid(row=0, column=0, columnspan=2, padx=(10, 10))
        self.vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.file_list_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.file_list_label.grid(row=0, column=0, columnspan=2, padx=(10, 10))
        self.file_box_frame.grid(row=1, column=0, columnspan=2, padx=(10, 10), sticky="ewns")
        self.add_file_button.grid(row=2, column=0, padx=(10, 0), pady=(10, 10), sticky="ew")
        self.rm_file_button.grid(row=2, column=1, padx=(0, 10), pady=(10, 10), sticky="ew")
        self.close_button.grid(row=3, column=0, columnspan=2, padx=(0, 10), pady=(5, 10), sticky="ew")
        self.canvas.get_tk_widget().grid(row=0, column=2, rowspan=2)
        self.export_button.grid(row=3, column=2, sticky="ew", pady=(10, 10))
        self.y_axis_label.grid(row=0, column=0, columnspan=2)
        self.y_axis_min_label.grid(row=1, column=0)
        self.y_axis_min_entry.grid(row=1, column=1, padx=(0, 15))
        self.y_axis_max_label.grid(row=2, column=0)
        self.y_axis_max_entry.grid(row=2, column=1, padx=(0, 15))
        self.x_axis_label.grid(row=3, column=0, columnspan=2)
        self.x_axis_min_label.grid(row=4, column=0)
        self.x_axis_min_entry.grid(row=4, column=1, padx=(0, 15))
        self.x_axis_max_label.grid(row=5, column=0)
        self.x_axis_max_entry.grid(row=5, column=1, padx=(0, 15))
        self.axis_apply.grid(row=6, column=0, columnspan=2, sticky="ew", padx=(0, 15))
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
                this_line = self.axes.plot(x, y, label=filename)
                self.lines_dict[filename] = this_line
                self.axes.legend(bbox_to_anchor=(.4, .2), loc='lower left', borderaxespad=0.)
                self.canvas.draw()
                
                # get current axes limits and update the text box
                self.update_axes_text()

    def update_axes_text(self):
        """
        update the entries with min/max values of the axes
        :return:
        """
        bottom, top = self.axes.get_ylim()
        left, right = self.axes.get_xlim()

        self.x_axis_min_entry.delete(0, "end")
        self.x_axis_min_entry.insert(0, left)
        self.x_axis_max_entry.delete(0, "end")
        self.x_axis_max_entry.insert(0, right)

        self.y_axis_min_entry.delete(0, "end")
        self.y_axis_min_entry.insert(0, bottom)
        self.y_axis_max_entry.delete(0, "end")
        self.y_axis_max_entry.insert(0, top)

    def remove_file(self):
        """remove_file
        """
        # remove the highlighted files from list and graph
        selection = self.file_list_box.curselection()
        for i in reversed(selection):
            filename = self.file_list_box.get(i)
            self.file_list_box.delete(i)
            line = self.lines_dict[filename]
            self.axes.lines.remove(line[0])
            self.axes.legend(bbox_to_anchor=(.4, .2), loc='lower left', borderaxespad=0.)
            self.canvas.draw()

        # self.file_list_box.delete(tk.ACTIVE)

    def save_plot(self):
        file_types = [('Portable Network Graphics (PNG)', '*.png'), ('Enhanced Post Script (EPS)', '*.eps'),
                      ('Portable Document Format (PDF)', '*.pdf'), ('Progressive Graphics File (PGF)', '*.pgf'),
                      ('PostScript (PS)', '*.ps'), ('Raw File', '*.raw'), ('RGBA file', '*.rgba'),
                      ('Scalable Vector Graphics (SVG)', '*.svg'), ('Compressed SVG (SVGZ)', '*.svgz')]
        save_file = tk.filedialog.asksaveasfilename(filetypes=file_types,
                                                    initialfile="relativeReflectance")
        self.fig.savefig(save_file)

    def apply_axis(self):
        xmin = float(self.x_axis_min_entry.get())
        xmax = float(self.x_axis_max_entry.get())
        ymin = float(self.y_axis_min_entry.get())
        ymax = float(self.y_axis_max_entry.get())

        self.axes.set_xlim(xmin, xmax)
        self.axes.set_ylim(ymin, ymax)
        self.canvas.draw()

    def back_button_pressed(self):
        self.window.withdraw()

    def _quit(self):
        self.window.quit()     # stops mainloop
        self.window.destroy()  # this is necessary on Windows to prevent
                               # Fatal Python Error: PyEval_RestoreThread: NULL tstate
