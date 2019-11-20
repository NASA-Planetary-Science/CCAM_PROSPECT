import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from pkg.InputType import InputType
from pkg.relativeReflectanceCalibration import RelativeReflectanceCalibration
from pkg.radianceCalibration import RadianceCalibration


class MainApplication(tk.Frame):
    input_type_switcher = {
        InputType.FILE.value: InputType.FILE,
        InputType.FILE_LIST.value: InputType.FILE_LIST,
        InputType.DIRECTORY.value: InputType.DIRECTORY
    }

    def __init__(self, window, *args, **kwargs):
        tk.Frame.__init__(self, window, *args, **kwargs)

        self.radiance_cal = RadianceCalibration(self)
        self.relative_cal = RelativeReflectanceCalibration(self)
        self.window = window
        self.progress_var = tk.IntVar()

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
        self.separator1 = ttk.Separator(window, orient="horizontal")
        self.out_label = tk.Label(window, text="Output Directory: ")
        self.out_directory_type = tk.IntVar()
        self.use_default_out_btn = tk.Radiobutton(window, text="Use default\n (same as input dir)", value=1,
                                                  variable=self.out_directory_type,
                                                  command=self.select_output_directory)
        self.use_default_out_btn.select()
        self.use_custom_out_btn = tk.Radiobutton(window, text="Use custom", value=2, variable=self.out_directory_type,
                                                 command=self.select_output_directory)
        self.out_directory_entry = tk.Entry(window, width=15, state="disabled")
        self.outBrowseBtn = tk.Button(window, text='Browse', command=self.out_clicked, state="disabled")

        # config stuff for relative reflectance
        self.separator2 = ttk.Separator(window, orient="horizontal")
        self.relative_config = tk.IntVar()
        self.relative_label = tk.Label(window, text="Relative Reflectance Calibration:")
        self.custom_file = tk.Entry(window, text="custom file", width=15, state="disabled")
        self.custom_file_browse = tk.Button(window, text="Browse", state="disabled", command=self.custom_browse_clicked)
        self.browseBtn = tk.Button(window, text='Browse', command=self.browse_clicked)
        self.use_default_btn = tk.Radiobutton(window, text="Use default\n (target 11 sol 76)", value=1,
                                              variable=self.relative_config, command=self.select_custom)
        self.use_default_btn.select()
        self.use_custom_btn = tk.Radiobutton(window, text="Use custom", value=2, variable=self.relative_config,
                                             command=self.select_custom)

        # 'GO' buttons
        self.separator3 = ttk.Separator(window, orient="horizontal")
        self.calibrate_rad_button = tk.Button(window, text="Calibrate to RAD", command=self.start_rad)
        self.calibrate_button = tk.Button(window, text="Calibrate to REF", command=self.start_calibration)

        # progress bar
        self.progress = ttk.Progressbar(window, orient=tk.HORIZONTAL, length=100, mode='determinate',
                                        var=self.progress_var, maximum=100)

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
        self.in_filename_entry.grid(column=0, row=2, columnspan=3, sticky="w", padx=(10, 0))
        self.browseBtn.grid(column=3, row=2, sticky="w")
        self.separator1.grid(column=0, row=4, columnspan=5, sticky="ew", pady=(10, 10))
        self.out_label.grid(column=0, row=6, columnspan=4, sticky="w", padx=(10, 0))

        self.use_default_out_btn.grid(column=0, row=7, rowspan=3, columnspan=3, sticky="w", padx=(10, 0))
        self.use_custom_out_btn.grid(column=2, row=7, rowspan=2, sticky="w")
        self.out_directory_entry.grid(column=2, row=9, columnspan=2)
        self.outBrowseBtn.grid(column=4, row=9, padx=(1, 10))
        self.separator2.grid(column=0, row=10, columnspan=5, sticky="ew", pady=(10, 10))
        self.relative_label.grid(column=0, row=11, columnspan=4, sticky="w", padx=(10, 0))
        self.use_default_btn.grid(column=0, row=12, rowspan=3, columnspan=3, sticky="w", padx=(10, 0))
        self.use_custom_btn.grid(column=2, row=12, rowspan=2, sticky="w")
        self.custom_file.grid(column=2, row=14, columnspan=2)
        self.custom_file_browse.grid(column=4, row=14, padx=(1, 10))

        self.separator3.grid(column=0, row=15, columnspan=5, sticky="ew", pady=(10, 10))
        self.calibrate_rad_button.grid(column=0, row=16, columnspan=2, sticky="ew", pady=(5, 0), padx=(20, 5))
        self.calibrate_button.grid(column=2, row=16, columnspan=2, sticky="ew", pady=(5, 0), padx=(5, 10))
        self.progress.grid(column=0, row=17, columnspan=5, sticky="ew", pady=(10, 10), padx=(5, 5))

    def browse_clicked(self):
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
        file = filedialog.askopenfilename()
        self.custom_file.delete(0, "end")
        self.custom_file.insert(0, file)

    def out_clicked(self):
        file = filedialog.askdirectory()
        self.out_directory_entry.delete(0, "end")
        self.out_directory_entry.insert(0, file)

    def select_custom(self):
        btn = self.relative_config.get()
        if btn == 1:
            self.custom_file.config(state="disabled")
            self.custom_file_browse.config(state="disabled")
        else:
            self.custom_file.config(state="normal")
            self.custom_file_browse.config(state="normal")

    def start_calibration(self):
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

        self.relative_cal.calibrate_relative_reflectance(file_type, file, custom_directory, out_dir)

    def start_rad(self):
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

        self.radiance_cal.calibrate_to_radiance(file_type, file, out_dir)

    def select_output_directory(self):
        btn = self.out_directory_type.get()
        if btn == 1:
            self.out_directory_entry.config(state="disabled")
            self.outBrowseBtn.config(state="disabled")
        else:
            self.out_directory_entry.config(state="normal")
            self.outBrowseBtn.config(state="normal")

    def update_progress(self, value):
        self.progress_var.set(value)
        self.progress.update()
        self.window.update_idletasks()


def main():
    window = tk.Tk()
    window.title("ChemCham Calibration")
    MainApplication(window)
    window.mainloop()
