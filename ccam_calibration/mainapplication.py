import tkinter as tk
from tkinter import filedialog, ttk, messagebox, Grid, N, S, E, W
from datetime import datetime
from ccam_calibration.utils.InputType import InputType
from ccam_calibration.relativeReflectanceCalibration import RelativeReflectanceCalibration
from ccam_calibration.radianceCalibration import RadianceCalibration
from ccam_calibration.plotpanel import PlotPanel


class MainApplication():
    input_type_switcher = {
        InputType.FILE.value: InputType.FILE,
        InputType.FILE_LIST.value: InputType.FILE_LIST,
        InputType.DIRECTORY.value: InputType.DIRECTORY
    }

    def __init__(self, root_window):
        """
        Initialize the GUI and its components
        """
        # tk.Frame.__init__(self, window, *args, **kwargs)

        Grid.columnconfigure(root_window, 2, weight=3)

        # create a log file to keep track of bad input
        now = datetime.now()
        self.logfile = "badInput_{}.log".format(now.strftime("%Y%m%d.%H%M%S"))
        open(self.logfile, 'a').close()  # open file so it exists

        # set up the calibration environments and the progress monitor
        self.radiance_cal = RadianceCalibration(self.logfile, self)
        self.relative_cal = RelativeReflectanceCalibration(self.logfile, self)
        self.window = root_window
        self.progress_var = tk.IntVar()
        self.overwrite_rad = tk.IntVar()
        self.overwrite_ref = tk.IntVar()
        self.overwrite_rad.set(1)
        self.overwrite_ref.set(1)

        # CREATE COMPONENTS

        # input label, entry, button
        self.input_label = tk.Label(self.window, text="Input: ")
        # radio button group and entries for input and output dir
        self.inputType = tk.IntVar()
        self.fileBtn = tk.Radiobutton(self.window, text='File', value=InputType.FILE.value, variable=self.inputType)
        self.fileBtn.select()  # select file by default
        self.listBtn = tk.Radiobutton(self.window, text='List Of Files', value=InputType.FILE_LIST.value,
                                      variable=self.inputType)
        self.directoryBtn = tk.Radiobutton(self.window, text='Directory', value=InputType.DIRECTORY.value,
                                           variable=self.inputType)
        self.in_filename_entry = tk.Entry(self.window, width=30)

        # output stuff
        self.separator1 = ttk.Separator(root_window, orient="horizontal")
        self.out_label = tk.Label(root_window, text="Output Directory: ")
        self.out_directory_type = tk.IntVar()
        self.use_default_out_btn = tk.Radiobutton(root_window, text="Use default\n (same as input dir)", value=1,
                                                  variable=self.out_directory_type,
                                                  command=self.select_output_directory)
        self.use_default_out_btn.select()
        self.use_custom_out_btn = tk.Radiobutton(root_window, text="Use custom", value=2, variable=self.out_directory_type,
                                                 command=self.select_output_directory)
        self.out_directory_entry = tk.Entry(root_window, width=15, state="disabled")
        self.outBrowseBtn = tk.Button(root_window, text='Browse', command=self.out_clicked, state="disabled")

        # config stuff for relative reflectance
        self.separator2 = ttk.Separator(root_window, orient="horizontal")
        self.relative_config = tk.IntVar()
        self.relative_label = tk.Label(root_window, text="Relative Reflectance Calibration:")
        self.custom_file = tk.Entry(root_window, text="custom file", width=15, state="disabled")
        self.custom_file_browse = tk.Button(root_window, text="Browse", state="disabled", command=self.custom_browse_clicked)
        self.browseBtn = tk.Button(root_window, text='Browse', command=self.browse_clicked)
        self.use_default_btn = tk.Radiobutton(root_window, text="Use default\n (target 11 sol 76)", value=1,
                                              variable=self.relative_config, command=self.select_custom)
        self.use_default_btn.select()
        self.use_custom_btn = tk.Radiobutton(root_window, text="Use custom", value=2, variable=self.relative_config,
                                             command=self.select_custom)

        # overwite file option buttons
        self.overwrite_rad_button = tk.Checkbutton(root_window, text="Overwrite existing RAD", variable=self.overwrite_rad)
        self.overwrite_ref_button = tk.Checkbutton(root_window, text="Overwrite existing REF", variable=self.overwrite_ref)

        # 'GO' buttons
        self.separator3 = ttk.Separator(root_window, orient="horizontal")
        self.calibrate_rad_button = tk.Button(root_window, text="Calibrate to RAD", width=20, command=self.start_rad)
        self.calibrate_button = tk.Button(root_window, text="Calibrate to REF", width=20, command=self.start_calibration)

        # progress bar
        self.progress = ttk.Progressbar(root_window, orient=tk.HORIZONTAL, length=100, mode='determinate',
                                        var=self.progress_var, maximum=100)

        # plotting
        self.separator4 = ttk.Separator(root_window, orient="horizontal")
        self.plot_button = tk.Button(root_window, text="Open Plotting", width=40, command=self.open_plots)

        self.set_up_layout()

    def set_up_layout(self):
        """
        set up the GUI layout
        :return: None
        """
        self.input_label.grid(column=0, row=0, columnspan=4, sticky="w", padx=(10, 0))
        self.fileBtn.grid(column=0, row=1, sticky="w", padx=(10, 0))
        self.listBtn.grid(column=1, row=1, sticky="w")
        self.directoryBtn.grid(column=2, row=1, sticky="w")
        self.in_filename_entry.grid(column=0, row=2, columnspan=3, sticky="ew", padx=(10, 0))
        self.browseBtn.grid(column=3, row=2, sticky="w")
        self.separator1.grid(column=0, row=4, columnspan=5, sticky="ew", pady=(10, 10))
        self.out_label.grid(column=0, row=6, columnspan=4, sticky="w", padx=(10, 0))

        self.use_default_out_btn.grid(column=0, row=7, rowspan=3, columnspan=3, sticky="w", padx=(10, 0))
        self.use_custom_out_btn.grid(column=2, row=7, rowspan=2, sticky="w")
        self.out_directory_entry.grid(column=2, row=9, columnspan=2, sticky="ew")
        self.outBrowseBtn.grid(column=4, row=9, padx=(1, 10))
        self.separator2.grid(column=0, row=10, columnspan=5, sticky="ew", pady=(10, 10))
        self.relative_label.grid(column=0, row=11, columnspan=4, sticky="w", padx=(10, 0))
        self.use_default_btn.grid(column=0, row=12, rowspan=3, columnspan=3, sticky="w", padx=(10, 0))
        self.use_custom_btn.grid(column=2, row=12, rowspan=2, sticky="w")
        self.custom_file.grid(column=2, row=14, columnspan=2, sticky="ew")
        self.custom_file_browse.grid(column=4, row=14, padx=(1, 10))

        self.separator3.grid(column=0, row=15, columnspan=5, sticky="ew", pady=(10, 10))
        self.overwrite_rad_button.grid(column=0, row=16, columnspan=2, sticky="w", pady=(5, 0), padx=(20, 5))
        self.overwrite_ref_button.grid(column=2, row=16, columnspan=2, sticky="w", pady=(5, 0), padx=(5, 10))
        self.calibrate_rad_button.grid(column=0, row=17, columnspan=2, sticky="w", pady=(5, 0), padx=(20, 5))
        self.calibrate_button.grid(column=2, row=17, columnspan=2, sticky="w", pady=(5, 0), padx=(5, 10))
        self.progress.grid(column=0, row=18, columnspan=5, sticky="ew", pady=(10, 10), padx=(5, 5))

        self.separator4.grid(column=0, row=19, columnspan=5, sticky="ew", pady=(10,10))
        self.plot_button.grid(column=0, row=20, columnspan=5, sticky="ew", pady=(10,10))

    def browse_clicked(self):
        """browse_clicked
        the action handler for the browse button to choose an input file
        """
        file_type = self.inputType.get()
        if file_type == InputType.FILE.value:  # file
            file = filedialog.askopenfilename()
        elif file_type == InputType.FILE_LIST.value:  # list of files
            file = filedialog.askopenfilename()
        elif file_type == InputType.DIRECTORY.value:  # directory
            file = filedialog.askdirectory()
            if not file.endswith("/"):
                file = file + "/"
        self.in_filename_entry.delete(0, "end")
        self.in_filename_entry.insert(0, file)

    def custom_browse_clicked(self):
        """custom_browse_clicked
        the action handler for the browse button to choose a custom set of
         files for the relative reflectance calculation
        """
        file = filedialog.askopenfilename()
        self.custom_file.delete(0, "end")
        self.custom_file.insert(0, file)

    def out_clicked(self):
        """out_clicked
        the action handler for the browse button to choose a
        custom output directory
        """
        file = filedialog.askdirectory()
        self.out_directory_entry.delete(0, "end")
        self.out_directory_entry.insert(0, file)

    def select_custom(self):
        """ select_custom
        the action handler for when a user selects to use a
        custom set of files for relative reflectance.  If default
        is selected, disable the custom options.
        """
        btn = self.relative_config.get()
        if btn == 1:
            self.custom_file.config(state="disabled")
            self.custom_file_browse.config(state="disabled")
        else:
            self.custom_file.config(state="normal")
            self.custom_file_browse.config(state="normal")

    def select_output_directory(self):
        """ select_output_directory
        the action handler for when a user selects to use a
        custom output directory.  If default is selected, disable
        the custom options.
        """
        btn = self.out_directory_type.get()
        if btn == 1:
            self.out_directory_entry.config(state="disabled")
            self.outBrowseBtn.config(state="disabled")
        else:
            self.out_directory_entry.config(state="normal")
            self.outBrowseBtn.config(state="normal")

    def update_progress(self, value):
        """update_progress
        update the progress bar to this given value
        :param: value the value to set the progress bar
        """
        self.progress_var.set(value)
        self.progress.update()
        self.window.update_idletasks()

    def start_calibration(self):
        """start_calibration
        gather variables and start the relative reflectance calibration
        """
        file_type = self.input_type_switcher.get(self.inputType.get(), "Not a valid input type")
        file = self.in_filename_entry.get()
        custom_directory = self.custom_file.get()
        output_type = self.out_directory_type.get()
        if output_type == 1:
            # use default
            out_dir = None
        else:
            out_dir = self.out_directory_entry.get()
            if not out_dir.endswith('/'):
                out_dir = out_dir + '/'

        try:
            self.relative_cal.calibrate_relative_reflectance(file_type, file, custom_directory, out_dir,
                                                             self.overwrite_rad.get(), self.overwrite_ref.get())
        except FileNotFoundError:
            input_type = 'File'
            if file_type.value is InputType.DIRECTORY.value:
                input_type = 'Directory'
            messagebox.showinfo('Error', 'The input {} ({}) does not exist'.format(input_type, file))
        print('******** finished calibration ********')

    def start_rad(self):
        """start_rad
        gather variables and start the radiance calibration
        """
        file_type = self.input_type_switcher.get(self.inputType.get(), "Not a valid input type")
        file = self.in_filename_entry.get()
        output_type = self.out_directory_type.get()
        if output_type == 1:
            # use default
            out_dir = None
        else:
            out_dir = self.out_directory_entry.get()
            if not out_dir.endswith('/'):
                out_dir = out_dir + '/'
        try:
            self.radiance_cal.calibrate_to_radiance(file_type, file, out_dir, self.overwrite_rad.get())
        except FileNotFoundError:
            input_type = 'File'
            if file_type.value is InputType.DIRECTORY.value:
                input_type = 'Directory'
            messagebox.showinfo('Error', 'The input {} ({}) does not exist'.format(input_type, file))
        print('******** finished calibration ********')

    def open_plots(self):
        """open_plots
        open the plotting window
        """
        self.window.withdraw()
        newWin = tk.Toplevel(self.window)
        PlotPanel(newWin)


def main():
    root_window = tk.Tk()
    root_window.title("ChemCham Calibration")
    MainApplication(root_window)
    root_window.mainloop()
