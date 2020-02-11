import numpy as np
import os
import argparse
from datetime import datetime
from ccam_calibration.utils.InputType import InputType
from ccam_calibration.utils.NonStandardExposureTimeException import NonStandardExposureTimeException
from ccam_calibration.utils.Utilities import get_integration_time, write_final, write_label
from ccam_calibration.radianceCalibration import RadianceCalibration


class RelativeReflectanceCalibration:
    def __init__(self, main_app=None):
        self.rad_file = ''
        self.wavelength = []
        self.main_app = main_app
        self.total_files = 1
        self.current_file = 1
        self.original_label = ""
        now = datetime.now()
        self.bad_exposure_file = "nonstandard_exptime_{}.log".format(now.strftime("%Y%m%d.%H%M%S"))
        open(self.bad_exposure_file, 'a').close()

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
        conv = os.path.join(sol76dir, 'Target11_60_95.txt.conv');
        values_conv = [float(x.split()[1].strip()) for x in open(conv).readlines()]

        # multiply original values by the appropriate calibration values
        # to get relative reflectance.
        c = np.multiply(values_conv, values)

        return c

    def get_rad_file(self, input_file, out_dir):
        """
        Get the rad file that we want to calibrate. This could be the input file,
        or we may have to first calibrate the input file to radiance.

        :param input_file: the file to calibrate
        :param out_dir: the chosen output directory
        :return:
        """
        # name of the rad file - replace psv with rad (or PSV with RAD)
        (path, filename) = os.path.split(input_file)
        rad_filename = filename.replace('psv', 'rad')
        rad_filename = rad_filename.replace('PSV', 'RAD')
        self.rad_file = os.path.join(path, rad_filename)

        # rename to .TAB from .TXT in case of raw input
        self.rad_file = self.rad_file.replace('.TXT', '.tab')
        self.rad_file = self.rad_file.replace('.txt', '.tab')

        exists = False
        if os.path.isfile(self.rad_file) and os.path.isfile(self.rad_file):
            if "rad" in self.rad_file.lower() and self.rad_file.lower().endswith(".tab"):
                return True
        if not exists:
            # create rad file and change path to where it will end up in out_dir
            if out_dir is not None:
                (path, filename) = os.path.split(self.rad_file)
                self.rad_file = os.path.join(out_dir, filename)
            else:
                (out_dir, filename) = os.path.split(input_file)
            if not out_dir.endswith('/'):
                out_dir = out_dir + '/'
            radiance_cal = RadianceCalibration()
            return radiance_cal.calibrate_to_radiance(InputType.FILE, input_file, out_dir)

    def choose_values(self, custom_target_file=None):
        """ choose_values
        Choose which values to use for calibration, based on integration time.  The integration
        time of the file chosen to calibrate must match that of the input file.  If the integration
        times do not match, log filename to nonstandard exptime file and keep going.

        :param custom_target_file: a custom file to use for calibration (default=None)
        :return: the values to use for calibration
        """
        if not custom_target_file:
            my_path = os.path.abspath(os.path.dirname(__file__))
            sol76dir = os.path.join(my_path, "sol76")
            ms7 = os.path.join(sol76dir, 'CL0_404238481PSV_F0050104CCAM02076P1.TXT.RAD.cor.7ms.txt.cos')
            ms34 = os.path.join(sol76dir, 'CL0_404238492PSV_F0050104CCAM02076P1.TXT.RAD.cor.34ms.txt.cos')
            ms404 = os.path.join(sol76dir, 'CL9_404238503PSV_F0050104CCAM02076P1.TXT.RAD.cor.404ms.txt.cos')
            ms5004 = os.path.join(sol76dir, 'CL9_404238538PSV_F0050104CCAM02076P1.TXT.RAD.cor.5004ms.txt.cos')
        else:
            ms7 = custom_target_file
            ms34 = custom_target_file
            ms404 = custom_target_file
            ms5004 = custom_target_file

        # now get the cosine-corrected values from the correct file
        # check t_int for file
        t_int = get_integration_time(self.rad_file)
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
            fn = None
            print('error - integration time in input file is not 7, 34, 404, or 5004. File tracked in log')
            with open(self.bad_exposure_file, 'a') as log:
                log.write(self.rad_file + '\n')
                raise NonStandardExposureTimeException('Exposure time is not one of 7, 34, 404, or 5004')

        if fn is not None:
            # get the values, but skip the header
            values = [float(x.split(' ')[1].strip()) for x in open(fn).readlines() if '"' not in x]
            # get the wavelengths
            self.wavelength = [float(x.split(' ')[0].strip()) for x in open(fn).readlines() if '"' not in x]

        return values

    def update_progress(self, value=None):
        """update_progress
        update progress on the main app
        """
        if self.main_app is not None:
            if value is not None:
                self.main_app.update_progress(value)
            else:
                if self.total_files is not 0:
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

    def calibrate_file(self, filename, custom_dir, out_dir):
        """calibrate_file
        calibrate the file to relative reflectance

        :param: filename the file to be calibrated
        :param: custom_dir the directory containing files to use for calibration if not default
        :param: out_dir the output directory for calibrated files
        """
        # check for valid rad file
        valid = self.get_rad_file(filename, out_dir)
        if valid:
            print('calibrating' + filename)
            # valid rad file
            # check for original label
            self.original_label = filename.replace('.tab', '.lbl')
            self.original_label = self.original_label.replace('.txt', '.lbl')
            self.original_label = self.original_label.replace('.TAB', '.lbl')
            self.original_label = self.original_label.replace('.TXT', '.lbl')
            self.original_label = self.original_label.replace('rad', 'psv')
            self.original_label = self.original_label.replace('RAD', 'PSV')
            try:
                # now choose values based on exp time
                values = self.choose_values(custom_dir)
                if self.total_files == 1:
                    self.update_progress(25)
                # then calibrate by dividing by values
                new_values = self.do_division(values)
                if self.total_files == 1:
                    self.update_progress(75)
                # convolve
                final_values = self.do_multiplication(new_values)

                # rename rad to ref to get outfile name and then write to file
                out_filename = self.rad_to_ref(out_dir)
                write_final(out_filename, self.wavelength, final_values)

                if os.path.exists(self.original_label):
                    # write new label based on original
                    (path, filename) = os.path.split(self.original_label)
                    new_label_filename = filename.replace('PSV', 'REF')
                    new_label_filename = new_label_filename.replace('psv', 'ref')
                    new_label_filename = new_label_filename.replace('lbl', 'xml')
                    (out_path, filename) = os.path.split(out_filename)
                    new_label = os.path.join(out_path, new_label_filename)
                    write_label(new_label, self.original_label, False)

                if self.total_files == 1:
                    self.update_progress(100)

                print(filename + ' calibrated and written to ' + out_filename)
            except NonStandardExposureTimeException:
                # this file has been logged, but keep going
                pass
        else:
            print(filename + ' not a valid raw (psv) or rad file.')

    def calibrate_directory(self, directory, custom_dir, out_dir):
        """calibrate_directory
        calibrate everything in this directory, recursively.

        :param: directory the directory in which to look for PSV or RAD files
        :param: out_dir the destination directory for output
        """
        self.total_files = sum([len(files) for r, d, files in os.walk(directory)])
        self.current_file = 1
        for file_name in os.listdir(directory):
            full_path = os.path.join(directory, file_name)
            if os.path.isdir(full_path) and full_path is not out_dir:
                self.calibrate_directory(os.path.join(directory, file_name), custom_dir, out_dir)
            else:
                self.calibrate_file(full_path, custom_dir, out_dir)
                self.current_file += 1
                self.update_progress()

        self.update_progress(100)

    def calibrate_list(self, list_file, custom_dir, out_dir):
        """calibrate_list
        calibrate everything in this list

        :param: list the list of psv or rad files to calibrate
        :param: out_dir the destination directory for output
        """
        files = open(list_file).read().splitlines()
        self.total_files = len(files)
        self.current_file = 1
        for file_name in files:
            self.calibrate_file(file_name, custom_dir, out_dir)
            self.current_file += 1
            self.update_progress()
        self.update_progress(100)

    def calibrate_relative_reflectance(self, file_type, file_name, custom_dir, out_dir):
        if file_type.value is InputType.FILE.value:
            self.calibrate_file(file_name, custom_dir, out_dir)
        elif file_type.value is InputType.FILE_LIST.value:
            self.calibrate_list(file_name, custom_dir, out_dir)
        else:
            self.calibrate_directory(file_name, custom_dir, out_dir)


if __name__ == "__main__":
    # create a command line parser
    parser = argparse.ArgumentParser(description='Relative Reflectance Calibration')
    parser.add_argument('-f', action="store", dest='ccamFile', help="CCAM psv or rad *.tab file")
    parser.add_argument('-d', action="store", dest='directory', help="Directory containing .tab files to calibrate")
    parser.add_argument('-l', action="store", dest='list', help="File with a list of .tab files to calibrate")
    parser.add_argument('-c', action="store", dest='customDir', help="directory containing custom calibration files")
    parser.add_argument('-o', action="store", dest='out_dir', help="directory to store the output files")

    args = parser.parse_args()
    if args.ccamFile is not None:
        in_file_type = InputType.FILE
        file = args.ccamFile
    elif args.directory is not None:
        in_file_type = InputType.DIRECTORY
        file = args.directory
    else:
        in_file_type = InputType.FILE_LIST
        file = args.list

    calibrate_ref = RelativeReflectanceCalibration()
    calibrate_ref.calibrate_relative_reflectance(in_file_type, file, args.customDir, args.out_dir)
