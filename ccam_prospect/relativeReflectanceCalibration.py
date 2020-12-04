import numpy as np
import os
import argparse
import sys
from datetime import datetime
from ccam_prospect.utils.InputType import InputType
from ccam_prospect.utils.CustomExceptions import InputFileNotFoundException, NonStandardHeaderException, \
    CancelExecutionException
from ccam_prospect.utils.Utilities import get_integration_time, write_final, write_label
from ccam_prospect.radianceCalibration import RadianceCalibration


class RelativeReflectanceCalibration:
    def __init__(self, log_file, main_app=None):
        self.rad_file = ''
        self.wavelength = []
        self.main_app = main_app
        self.total_files = 1
        self.current_file = 1
        self.logfile = log_file
        self.show_mismatched_warning = True   # show dialog for mismatched exposure time
        self.show_exposure_warning = True     # show dialog for nonstandard exposure time
        self.show_header_warning = True       # show dialog for nonstandard header
        self.show_list_warning = True         # show dialog for file in list doesn't exist

    def do_division(self, values):
        """
        Divide each value in the file by the calibration values

        :param values:
        :return: the divided values
        """
        with open(self.rad_file) as f:
            values_orig = [float(x.split()[1].strip()) for index, x in enumerate(f) if index > 28]

        # divide original values by the appropriate calibration values
        # to get relative reflectance.  If divide by 0, just = 0
        with np.errstate(divide='ignore', invalid='ignore'):
            c = np.true_divide(values_orig, values)
            c[c == np.inf] = 0
            c = np.nan_to_num(c)

        return c

    @staticmethod
    def do_multiplication(values):
        """
        Multiply each value in the file by the lab bidirectional spectrum value

        :param values:
        :return: multiplied values
        """
        my_path = os.path.abspath(os.path.dirname(__file__))
        sol76dir = os.path.join(my_path, "sol76")
        convolve = os.path.join(sol76dir, 'Target11_60_95.txt.conv')
        values_conv = [float(x.split()[1].strip()) for x in open(convolve).readlines()]

        # multiply original values by the appropriate calibration values
        # to get relative reflectance.
        c = np.multiply(values_conv, values)

        return c

    @staticmethod
    def get_rad_filename(input_file):
        """get_rad_filename
        create the filename of the corresponding rad file to this psv file
        :param: input_file: the input psv file
        """
        # replace PSV with RAD
        (path, filename) = os.path.split(input_file)
        rad_filename = filename.replace('psv', 'rad')
        rad_filename = rad_filename.replace('PSV', 'RAD')
        rad_file = os.path.join(path, rad_filename)

        # rename to .TAB from .TXT in case of raw input
        rad_file = rad_file.replace('.TXT', '.tab')
        rad_file = rad_file.replace('.txt', '.tab')

        return rad_file

    def get_rad_file(self, input_file, out_dir, overwrite_rad):
        """
        Get the rad file that we want to calibrate. This could be the input file,
        or we may have to first calibrate the input file to radiance.

        :param input_file: the file to calibrate
        :param out_dir: the chosen output directory
        :param overwrite_rad: boolean to overwrite existing rad file
        :return boolean: there is a valid RAD file and/or we created one. We can proceed with calibration.
        """
        # name of the rad file - replace psv with rad (or PSV with RAD)
        self.rad_file = self.get_rad_filename(input_file)

        if os.path.isfile(self.rad_file) and not overwrite_rad:
            # rad file already exists and we don't want to overwrite, return
            if "rad" in self.rad_file.lower() and self.rad_file.lower().endswith(".tab"):
                return True

        # rad file does not yet exist - let's create it first.
        # create rad file and change path to where it will end up in out_dir
        if out_dir is not None:
            (path, filename) = os.path.split(self.rad_file)
            self.rad_file = os.path.join(out_dir, filename)
        else:
            (out_dir, filename) = os.path.split(input_file)
        radiance_cal = RadianceCalibration(self.logfile, self.main_app)
        return radiance_cal.calibrate_to_radiance(InputType.FILE, input_file, out_dir, overwrite_rad)

    def choose_values(self, custom_target_file=None):
        """ choose_values
        Choose which values to use for calibration, based on integration time.  The integration
        time of the file chosen to calibrate must match that of the input file.  If the integration
        times do not match, log filename to nonstandard exptime file and keep going.

        :param custom_target_file: a custom file to use for calibration (default=None)
        :return: the values to use for calibration
        """
        if not custom_target_file:
            # built-in target files
            my_path = os.path.abspath(os.path.dirname(__file__))
            sol76dir = os.path.join(my_path, "sol76")
            ms7 = os.path.join(sol76dir, 'CL0_404238481PSV_F0050104CCAM02076P1.TXT.RAD.cor.7ms.txt.cos')
            ms34 = os.path.join(sol76dir, 'CL0_404238492PSV_F0050104CCAM02076P1.TXT.RAD.cor.34ms.txt.cos')
            ms404 = os.path.join(sol76dir, 'CL9_404238503PSV_F0050104CCAM02076P1.TXT.RAD.cor.404ms.txt.cos')
            ms5004 = os.path.join(sol76dir, 'CL9_404238538PSV_F0050104CCAM02076P1.TXT.RAD.cor.5004ms.txt.cos')
        else:
            # using a custom target file, set it to each integration time
            #    - will be checked for matching time later
            ms7 = custom_target_file
            ms34 = custom_target_file
            ms404 = custom_target_file
            ms5004 = custom_target_file

        # now get the cosine-corrected values from the correct file
        # calculate integration time for the file that is being calibrated
        try:
            t_int = get_integration_time(self.rad_file)
        except NonStandardHeaderException:
            warning = self.rad_file + ': not a valid RAD file header. Skipping this file.'
            # write to log file
            with open(self.logfile, 'a+') as log:
                log.write(self.rad_file + ': relative reflectance calibration - ' + warning + '\n')
            if self.show_header_warning:
                print('error - ' + warning + ' File tracked in log')
                # show warning
                if self.main_app is not None:
                    self.show_header_warning = self.main_app.show_warning_dialog(warning)
            if self.show_header_warning is None:
                # cancel
                raise CancelExecutionException
            # exit because file was invalid
            return None

        if t_int is not None:
            t_int = round(t_int * 1000)

        if t_int == 7:
            fn = ms7
        elif t_int == 34:
            fn = ms34
        elif t_int == 404:
            fn = ms404
        elif t_int == 5004:
            fn = ms5004
        else:
            warning = self.rad_file + ': Exposure time is not one of 7, 34, 404, or 5004. Skipping this file.'
            print('Warning: ' + warning + ' File tracked in log')
            # track in log file
            with open(self.logfile, 'a+') as log:
                log.write(self.rad_file + ': relative reflectance calibration - ' + warning + ' \n')
            if self.show_exposure_warning:
                # show warning
                if self.main_app is not None:
                    self.show_exposure_warning = self.main_app.show_warning_dialog(warning)
            if self.show_exposure_warning is None:
                # cancel
                raise CancelExecutionException
            # return from this function
            return None

        if fn is not None:
            # if using a custom file, check that the custom exposure time and input exposure times match.
            # If they don't - throw an error, log in file, and
            if custom_target_file:
                t_int_custom = get_integration_time(custom_target_file)
                t_int_custom = round(t_int_custom * 1000)
                if t_int_custom != t_int:
                    warning = 'integration times between input file ' + self.rad_file + ' (' + str(t_int) + ')'\
                        ' and custom target file ' + str(custom_target_file) + ' (' + str(t_int_custom) + ') ' \
                        ' do not match. Skipping this file.'
                    # write to log file
                    with open(self.logfile, 'a+') as log:
                        log.write(self.rad_file + ': relative reflectance calibration - custom target file'
                                                  ' integration time does not match.\n')
                    print('****************************\n '
                          'WARNING: ' + warning + ' \n****************************\n ')
                    if self.show_mismatched_warning:
                        # show warning dialog
                        if self.main_app is not None:
                            self.show_mismatched_warning = self.main_app.show_warning_dialog(warning)
                    if self.show_mismatched_warning is None:
                        # cancel
                        raise CancelExecutionException
                    # return from this function
                    return None

            # valid file with correct integration time. -
            # get the values, but skip the header
            values = [float(x.split()[1].strip()) for x in open(fn).readlines() if '"' not in x]
            # get the wavelengths
            self.wavelength = [float(x.split()[0].strip()) for x in open(fn).readlines() if '"' not in x]

        return values

    def update_progress(self, value=None):
        """update_progress
        update progress on the main app
        """
        if self.main_app is not None:
            if value is not None:
                self.main_app.update_progress(value)
            else:
                if self.total_files != 0:
                    self.main_app.update_progress((self.current_file / self.total_files) * 100)

    def rad_to_ref(self, out_dir):
        """rad_to_ref
        rename rad file to ref.
        """
        out_filename = self.rad_file.replace('RAD', 'REF')
        out_filename = out_filename.replace('rad', 'ref')
        if out_dir is not None:
            # then save calibrated file to out dir also
            (path, filename) = os.path.split(out_filename)
            out_filename = os.path.join(out_dir, filename)

        return out_filename

    @staticmethod
    def get_original_label(filename):
        """get_original_label
        the filename of the label for the input psv file.  should be a.lbl file """
        original_label = filename.replace('.tab', '.lbl')
        original_label = original_label.replace('.txt', '.lbl')
        original_label = original_label.replace('.TAB', '.lbl')
        original_label = original_label.replace('.TXT', '.lbl')
        original_label = original_label.replace('rad', 'psv')
        original_label = original_label.replace('RAD', 'PSV')
        return original_label

    def calibrate_file(self, filename, custom_file, out_dir, overwrite_rad, overwrite_ref):
        """calibrate_file
        calibrate the file to relative reflectance

        :param filename: the file to be calibrated
        :param custom_file: the file to use for calibration if not default
        :param out_dir: the output directory for calibrated files
        :param overwrite_rad: boolean to overwrite radiance files
        :param overwrite_ref: boolean to overwrite relative reflectance files
        """
        # check for valid rad file
        valid = self.get_rad_file(filename, out_dir, overwrite_rad)

        if valid:
            # valid rad file
            print('calibrating' + filename)

            out_filename = self.rad_to_ref(out_dir)
            if not overwrite_ref:
                # if we don't want to overwrite existing files, we can skip this file if it already exists
                if os.path.exists(out_filename) and os.path.isfile(out_filename):
                    print(out_filename + " already exists, skipping")
                    return

            # now choose values based on exp time
            values = self.choose_values(custom_file)
            if values is None:
                return
            if self.total_files == 1:
                self.update_progress(25)
            # then calibrate by dividing by values
            new_values = self.do_division(values)
            if self.total_files == 1:
                self.update_progress(75)
            # convolve
            final_values = self.do_multiplication(new_values)

            # rename rad to ref to get outfile name and then write to file
            write_final(out_filename, self.wavelength, final_values)

            # check for original label
            original_label = self.get_original_label(filename)
            if os.path.exists(original_label):
                # write new label based on original
                (path, label_name) = os.path.split(original_label)
                new_label_filename = label_name.replace('PSV', 'REF')
                new_label_filename = new_label_filename.replace('psv', 'ref')
                new_label_filename = new_label_filename.replace('lbl', 'xml')
                (out_path, filename) = os.path.split(out_filename)
                new_label = os.path.join(out_path, new_label_filename)
                write_label(new_label, original_label, False)

            if self.total_files == 1:
                self.update_progress(100)

            print(filename + ' calibrated and written to ' + out_filename)

        else:
            ext = os.path.splitext(filename)[1]
            if ext != '.lbl' and ext != '.LBL' and ext != '.xml' and ext != '.log':
                # log file as long as its not a label to a psv file or a log file.
                with open(self.logfile, 'a+') as log:
                    log.write(filename + ': relative reflectance input - not a valid PSV or RAD file \n')

    def calibrate_directory(self, directory, custom_file, out_dir, overwrite_rad, overwrite_ref):
        """calibrate_directory
        calibrate everything in this directory, recursively.

        :param directory: the directory in which to look for PSV or RAD files
        :param custom_file: custom calibration file
        :param out_dir: the destination directory for output
        :param overwrite_rad: boolean to overwrite radiance files
        :param overwrite_ref: boolean to overwrite relative reflectance files
        """
        self.total_files = sum([len(files) for r, d, files in os.walk(directory)])
        self.current_file = 1
        try:
            for file_name in os.listdir(directory):
                # check each file in directory (file or subdirectory?)
                full_path = os.path.join(directory, file_name)
                if os.path.isdir(full_path) and full_path is not out_dir:
                    # recursive call for each subdirectory
                    self.calibrate_directory(os.path.join(directory, file_name), custom_file, out_dir,
                                             overwrite_rad, overwrite_ref)
                else:
                    # calibrate each file individually
                    self.calibrate_file(full_path, custom_file, out_dir, overwrite_rad, overwrite_ref)
                    self.current_file += 1
                    self.update_progress()
        except FileNotFoundError:
            print(directory + ": directory does not exist.")
            with open(self.logfile, 'a+') as log:
                log.write(directory + ': relative reflectance input - directory does not exist \n')
            if self.main_app is not None:
                raise InputFileNotFoundException(directory)
        self.update_progress(100)

    def calibrate_list(self, list_file, custom_file, out_dir, overwrite_rad, overwrite_ref):
        """calibrate_list
        calibrate everything in this list

        :param list_file: the list of psv or rad files to calibrate
        :param custom_file: custom calibration file
        :param out_dir: the destination directory for output
        :param overwrite_rad: boolean to overwrite radiance files
        :param overwrite_ref: boolean to overwrite relative reflectance files
        """
        try:
            # read each line into a list of files
            files = open(list_file).read().splitlines()
        except FileNotFoundError:
            print(list_file + ": file does not exist")
            with open(self.logfile, 'a+') as log:
                log.write(list_file + ':   relative reflectance input: file does not exist \n')
            if self.main_app is not None:
                raise InputFileNotFoundException(list_file)
            return
        self.total_files = len(files)
        self.current_file = 1
        for file_name in files:
            try:
                # calibrate each file in the list
                self.calibrate_file(file_name, custom_file, out_dir, overwrite_rad, overwrite_ref)
                self.current_file += 1
                self.update_progress()
            except InputFileNotFoundException:
                warning = file_name + ": file not found. Skipping this file."
                if self.show_list_warning:
                    if self.main_app is not None:
                        self.show_list_warning = self.main_app.show_warning_dialog(warning)
                if self.show_list_warning is None:
                    # cancel
                    raise CancelExecutionException
        self.update_progress(100)

    def calibrate_relative_reflectance(self, file_type, file_name, custom_file, out_dir, overwrite_rad, overwrite_ref):
        """calibrate_relative_reflectance
        start the calibration for file, list of files, or directory.

        :param file_type: the type of input: list, file, or directory.
        :param file_name: the input file
        :param custom_file: if there is a custom file relative reflectance
        :param out_dir: the output directory
        :param overwrite_rad: boolean to overwrite radiance files
        :param overwrite_ref: boolean to overwrite relative reflectance files
        :return:
        """
        if file_type.value is InputType.FILE.value:
            self.calibrate_file(file_name, custom_file, out_dir, overwrite_rad, overwrite_ref)
        elif file_type.value is InputType.FILE_LIST.value:
            self.calibrate_list(file_name, custom_file, out_dir, overwrite_rad, overwrite_ref)
        else:
            self.calibrate_directory(file_name, custom_file, out_dir, overwrite_rad, overwrite_ref)


if __name__ == "__main__":
    # create a command line parser
    parser = argparse.ArgumentParser(description='Relative Reflectance Calibration')
    parser.add_argument('-f', action="store", dest='ccamFile', help="CCAM psv or rad *.tab file")
    parser.add_argument('-d', action="store", dest='directory', help="Directory containing .tab files to calibrate")
    parser.add_argument('-l', action="store", dest='list', help="File with a list of .tab files to calibrate")
    parser.add_argument('-c', action="store", dest='customFile', help="custom calibration file")
    parser.add_argument('-o', action="store", dest='out_dir', help="directory to store the output files")
    parser.add_argument('--no-overwrite-rad', action="store_false", dest='overwrite_rad',
                        help="do not overwrite existing RAD files")
    parser.add_argument('--no-overwrite-ref', action="store_false", dest='overwrite_ref',
                        help="do not overwrite existing REF files")
    parser.set_defaults(overwrite_rad=True, overwrite_ref=True)

    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    if args.ccamFile is not None:
        in_file_type = InputType.FILE
        file = args.ccamFile
    elif args.directory is not None:
        in_file_type = InputType.DIRECTORY
        file = args.directory
    else:
        in_file_type = InputType.FILE_LIST
        file = args.list

    start_calibration = True

    out_dir = args.out_dir
    if out_dir is not None:
        if not out_dir.endswith('/'):
            out_dir = out_dir + '/'
            if not os.path.isdir(out_dir):
                print('output directory: ' + out_dir + ' does not exist. Please enter an existing directory.')
                start_calibration = False

    if start_calibration:
        overwrite_rad = args.overwrite_rad
        overwrite_ref = args.overwrite_ref

        now = datetime.now()
        logfile = "badInput_{}.log".format(now.strftime("%Y%m%d.%H%M%S"))

        calibrate_ref = RelativeReflectanceCalibration(logfile)
        calibrate_ref.calibrate_relative_reflectance(in_file_type, file, args.customFile, out_dir, overwrite_rad,
                                                     overwrite_ref)
