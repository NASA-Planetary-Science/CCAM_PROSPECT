import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# Implement the default Matplotlib key bindings.
from matplotlib.figure import Figure, GridSpec
from matplotlib import pyplot
import os
from ccam_prospect.utils.InputType import InputType, input_type_switcher
import numpy as np


def moving_median_smoothing(data, kernel_size):
    """
    smooth the data using a median filter with the given kernel size. if kernel size is 50,
    we will use the 25 values on either side.
    :param data:
    :param kernel_size:
    :return:
    """
    length = len(data);
    half_kernel = int(kernel_size / 2)
    smoothed = np.zeros(length)
    for t in range(length):
        if t <= half_kernel:
            half_kernel_old = half_kernel
            half_kernel = t - 1
        elif t > length - half_kernel:
            half_kernel_old = half_kernel
            half_kernel = t - 1
        if t == 0 or t == length - 1:
            # for first value and last value, just copy the data
            smoothed[t] = data[t]
        else:
            smoothed[t] = np.median(data[t - half_kernel:t + half_kernel + 1])
        half_kernel = half_kernel_old
    return np.array(smoothed)


def extract_floats(data, index):
    """
    extract the x or y data from each line, given 0 (x) or 1 (y)
    """
    return np.array([float(line.split()[index].strip()) for line in data])


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
        tk.Grid.columnconfigure(window, 4, weight=3)

        self.filename_dict = {}
        self.lines_dict = {}
        self.show_legend = tk.IntVar()

        self.file_box_frame = tk.Frame(self.window)
        self.axis_adjust_frame = tk.Frame(self.window)
        self.add_remove_frame = tk.Frame(self.window)

        self.file_list_label = tk.Label(self.window, text="Files: ")
        self.v_scrollbar = tk.Scrollbar(self.file_box_frame, orient=tk.VERTICAL)
        self.h_scrollbar = tk.Scrollbar(self.file_box_frame, orient=tk.HORIZONTAL)
        self.file_list_box = tk.Listbox(self.file_box_frame, selectmode="extended",
                                        width=30, yscrollcommand=self.v_scrollbar.set,
                                        xscrollcommand=self.h_scrollbar.set)
        self.v_scrollbar.config(command=self.file_list_box.yview)
        self.h_scrollbar.config(command=self.file_list_box.xview)

        self.file_type_label = tk.Label(self.add_remove_frame, text="Add From: ")
        # radio button group and entries for input file or directory
        self.inputType = tk.IntVar()
        self.fileBtn = tk.Radiobutton(self.add_remove_frame, text='File',
                                      value=InputType.FILE.value, variable=self.inputType)
        self.fileBtn.select()  # select file by default
        self.directoryBtn = tk.Radiobutton(self.add_remove_frame, text='Directory', value=InputType.DIRECTORY.value,
                                           variable=self.inputType)

        self.add_file_button = tk.Button(self.add_remove_frame, text="Add REF Files", command=self.add_files)
        self.rm_file_button = tk.Button(self.add_remove_frame, text="  Remove Selected  ", command=self.remove_file)

        self.fig = Figure(figsize=(10, 4), dpi=100)
        self.fig.text(.14, 0.75, '(VIO region\nsmoothed)', fontsize=10)
        self.gridspec = GridSpec(1, 2, width_ratios=[3.5, 1])
        self.axes = self.fig.add_subplot(self.gridspec[0,0])
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        self.axes.set_ylabel('Relative Reflectance')
        self.axes.set_xlabel('Wavelength (nm)')

        self.y_axis_min_label = tk.Label(self.axis_adjust_frame, text="min: ")
        self.y_axis_max_label = tk.Label(self.axis_adjust_frame, text="max: ")
        self.y_axis_min_entry = tk.Entry(self.axis_adjust_frame, width=10)
        self.y_axis_max_entry = tk.Entry(self.axis_adjust_frame, width=10)
        self.y_axis_label = tk.Label(self.axis_adjust_frame, text="Y-Axis: ")
        self.x_axis_min_label = tk.Label(self.axis_adjust_frame, text="min: ")
        self.x_axis_max_label = tk.Label(self.axis_adjust_frame, text="max: ")
        self.x_axis_min_entry = tk.Entry(self.axis_adjust_frame, width=10)
        self.x_axis_max_entry = tk.Entry(self.axis_adjust_frame, width=10)
        self.x_axis_label = tk.Label(self.axis_adjust_frame, text="X-Axis: ")
        self.title_label = tk.Label(self.axis_adjust_frame, text="Title: ")
        self.title_entry = tk.Entry(self.axis_adjust_frame)
        self.axis_apply = tk.Button(self.axis_adjust_frame, text="Apply", command=self.apply_axis)
        self.show_legend_button = tk.Checkbutton(self.axis_adjust_frame, text="Show Legend",
                                                 variable=self.show_legend, onvalue=1,
                                                 offvalue=0, command=self.show_legend_selected)
        self.show_legend_button.select()
        self.export_button = tk.Button(self.axis_adjust_frame, text="Save Plot", command=self.save_plot)
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
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.file_list_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=2)
        self.file_list_label.grid(row=0, column=0, columnspan=4, padx=(10, 10))
        self.file_box_frame.grid(row=1, column=0, columnspan=4, padx=(10, 10), sticky="ewns")

        self.file_type_label.grid(row=1, column=0, padx=(10, 1))
        self.fileBtn.grid(row=1, column=1)
        self.directoryBtn.grid(row=1, column=2)
        self.add_file_button.grid(row=0, column=0, columnspan=3, padx=(10, 10), pady=(10, 10), sticky="ew")
        self.rm_file_button.grid(row=0, column=3, padx=(5, 10), pady=(10, 10), sticky="ew")

        self.add_remove_frame.grid(row=3, column=0)
        self.close_button.grid(row=4, column=0, columnspan=4, padx=(0, 10), pady=(5, 10), sticky="ews")

        self.canvas.get_tk_widget().grid(row=0, column=4, rowspan=3, columnspan=3)
        self.y_axis_label.grid(row=0, column=0)
        self.y_axis_min_label.grid(row=0, column=1)
        self.y_axis_min_entry.grid(row=0, column=2, padx=(0, 15))
        self.y_axis_max_label.grid(row=0, column=3)
        self.y_axis_max_entry.grid(row=0, column=4, padx=(0, 15))
        self.x_axis_label.grid(row=1, column=0)
        self.x_axis_min_label.grid(row=1, column=1)
        self.x_axis_min_entry.grid(row=1, column=2, padx=(0, 15))
        self.x_axis_max_label.grid(row=1, column=3)
        self.x_axis_max_entry.grid(row=1, column=4, padx=(0, 15))
        self.title_label.grid(row=2, column=0)
        self.title_entry.grid(row=2, column=1, columnspan=4, sticky="ew")
        self.axis_apply.grid(row=3, column=0, columnspan=5, sticky="ew", padx=(0, 15))
        self.show_legend_button.grid(row=1, column=5, padx=(0,10), sticky="w")
        self.export_button.grid(row=2, column=5, pady=(0, 10), sticky="ew")
        self.axis_adjust_frame.grid(row=3, column=4, pady=(20, 10), padx=(0, 0))

    @staticmethod
    def read_file(file_name):
        x = []
        y = []
        with open(file_name) as f:
            # only plot data in the following ranges: 400 to 467nm, 477 to 840 nm
            # for 400 to 467 nm, use a 51-channel filter
            lines = f.readlines()
            all_data = [line for index, line in enumerate(lines) if 2428 < index < 5810]
            smooth_data = [line for index, line in enumerate(lines) if 2428 < index < 4039]
            other_data = [line for index, line in enumerate(lines) if 4120 < index < 5810]

            # smooth the data between 400 and 467
            y_smoothed = moving_median_smoothing(extract_floats(smooth_data, 1), 50)

            # get non-smoothed data and combine with smoothed data
            y = np.concatenate((y_smoothed, np.full(shape=82, fill_value=np.nan), extract_floats(other_data, 1)))

            # get x data from each set and combine
            x = extract_floats(all_data, 0)

        return x, y

    def add_files(self):
        # open file or directory?
        file_type = input_type_switcher.get(self.inputType.get(), "Not a valid input type")

        if file_type.value is InputType.FILE.value:
            self.add_file()
        elif file_type.value is InputType.DIRECTORY.value:
            self.add_directory()

    def add_file(self):
        """add_file
        """
        # open file chooser, select file
        ftypes = [('TAB files', ('*.tab', '*.TAB'))]
        files = tk.filedialog.askopenfilenames(filetypes=ftypes)

        # add file to list
        list_of_files = self.window.tk.splitlist(files)
        for current_file in list_of_files:
            self.plot_file(current_file)

    def add_directory(self):
        """add_directory
        """
        # open file chooser, select file
        directory = tk.filedialog.askdirectory()
        if directory:
            for file_name in os.listdir(directory):
                if file_name.endswith(".tab") or file_name.endswith(".TAB"):
                    current_file = os.path.join(directory, file_name)
                    self.plot_file(current_file)

    def plot_file(self, file):
        if "ref" in file or "REF" in file:
            (path, filename) = os.path.split(file)
            self.filename_dict[filename] = path
            self.file_list_box.insert(tk.END, filename)

            cols = 1
            if self.file_list_box.size() > 18:
                cols = 2

            # add file to graph
            # Data for plotting
            x, y = self.read_file(file)
            short_name = "{}_{}".format(filename[0:13], filename[29:34])
            this_line = self.axes.plot(x, y, label=short_name)
            self.lines_dict[short_name] = this_line
            self.show_legend_selected()
            self.canvas.draw()

            # get current axes limits and update the text box
            self.update_axes_text()

    def update_axes_text(self):
        """
        update the entries with min/max values of the axes
        :return:
        """
        bottom, top = self.axes.get_ylim()
        # adjust to 0 to 1 if outside of that range
        if bottom < 0:
            bottom = 0
        if top > 1:
            top = 1
        left, right = self.axes.get_xlim()

        self.x_axis_min_entry.delete(0, "end")
        self.x_axis_min_entry.insert(0, left)
        self.x_axis_max_entry.delete(0, "end")
        self.x_axis_max_entry.insert(0, right)

        self.y_axis_min_entry.delete(0, "end")
        self.y_axis_min_entry.insert(0, bottom)
        self.y_axis_max_entry.delete(0, "end")
        self.y_axis_max_entry.insert(0, top)

        self.apply_axis()

    def remove_file(self):
        """remove_file
        """
        selection = self.file_list_box.curselection()

        # remove the highlighted files from list and graph
        for i in reversed(selection):
            filename = self.file_list_box.get(i)
            self.file_list_box.delete(i)
            short_name = "{}_{}".format(filename[0:13], filename[29:34])
            line = self.lines_dict[short_name]
            self.axes.lines.remove(line[0])

        self.show_legend_selected()
        self.canvas.draw()

    def save_plot(self):
        """save_plot
        get file types and save plot as image
        """
        file_types = [('Portable Network Graphics (PNG)', '*.png'), ('Enhanced Post Script (EPS)', '*.eps'),
                      ('Portable Document Format (PDF)', '*.pdf'), ('Progressive Graphics File (PGF)', '*.pgf'),
                      ('PostScript (PS)', '*.ps'), ('Raw File', '*.raw'), ('RGBA file', '*.rgba'),
                      ('Scalable Vector Graphics (SVG)', '*.svg'), ('Compressed SVG (SVGZ)', '*.svgz')]
        initial_file = "relativeReflectance"
        if self.title_entry.get():
            initial_file = self.title_entry.get()
            initial_file = initial_file.replace(" ", "")
        save_file = tk.filedialog.asksaveasfilename(filetypes=file_types,
                                                    initialfile=initial_file)
        self.fig.savefig(save_file)

    def apply_axis(self):
        """apply_axis
        set axes limits based on user input
        """
        # gather min/max from input
        xmin = float(self.x_axis_min_entry.get())
        xmax = float(self.x_axis_max_entry.get())
        ymin = float(self.y_axis_min_entry.get())
        ymax = float(self.y_axis_max_entry.get())

        # set axes limits
        self.axes.set_xlim(xmin, xmax)
        self.axes.set_ylim(ymin, ymax)

        # set title based on user input
        title = str(self.title_entry.get())
        self.axes.set_title(title)

        self.canvas.draw()

    def show_legend_selected(self):
        """show_legend_selected
        turn legend on or off depending on selected button
        """
        cols = 1
        if self.file_list_box.size() > 20:
            cols = 2
        show = self.show_legend.get()
        if show:
            if len(self.axes.lines) > 0:
                self.axes.legend(bbox_to_anchor=(1.01, 1), loc='upper left', borderaxespad=0., ncol=cols,
                                 fontsize=7).set_draggable(True)
        else:
            if self.axes.get_legend() is not None:
                self.axes.get_legend().remove()
        self.canvas.draw()

    def back_button_pressed(self):
        self.window.withdraw()

    def _quit(self):
        self.window.quit()     # stops mainloop
        self.window.destroy()  # this is necessary on Windows to prevent
                               # Fatal Python Error: PyEval_RestoreThread: NULL tstate
