import numpy as np
import os
import argparse
from datetime import datetime
from shutil import copyfile
from pkg.NonStandardExposureTimeException import NonStandardExposureTimeException
from pkg.Utilities import get_integration_time, write_final
from pkg.radianceCalibration import RadianceCalibration
from pkg.InputType import InputType


class RelativeReflectanceCalibration:
    def __init__(self, main_app=None):
        self.psvfile = ''
        self.radfile = ''
        self.wavelength = []
        self.main_app = main_app
        self.total_files = 1
        self.current_file = 1
        now = datetime.now()
        self.bad_exposure_file = "nonstandard_exptime_{}.log".format(now.strftime("%Y%m%d.%H%M%S"))

    def do_division(self, values):
        """
        Divide each value in the file by the calibration values

        :param values:
        :return: the divided values
        """
        values_orig = [float(x.split(' ')[1].strip()) for x in open(self.radfile).readlines() if '"' not in x]

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
        sol76dir = os.path.join(my_path, "../sol76")
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
        # name of the rad file
        self.radfile = input_file.replace('psv', 'rad')
        self.psvfile = input_file.replace('rad', 'psv')
        exists = os.path.isfile(self.radfile)
        if not exists:
            # create rad file and change path to where it will end up in out_dir
            if out_dir is not None:
                (path, filename) = os.path.split(self.radfile)
                self.radfile = os.path.join(out_dir, filename)
            else:
                (out_dir, filename) = os.path.split(input_file)
            if not out_dir.endswith('/'):
                out_dir = out_dir + '/'
            radiance_cal = RadianceCalibration()
            return radiance_cal.calibrate_to_radiance(InputType.FILE, input_file, out_dir)
        else:
            return True

    def choose_values(self, custom_target_file=None):
        """
        Choose which values to use for calibration, based on integration time.  The integration
        time of the file chosen to calibrate must match that of the input file.  If the integration
        times do not match, log filename to nonstandard exptime file and keep going.

        :param custom_target_file: a custom file to use for calibration (default=None)
        :return: the values to use for calibration
        """
        if not custom_target_file:
            my_path = os.path.abspath(os.path.dirname(__file__))
            sol76dir = os.path.join(my_path, "../sol76")
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
        t_int = get_integration_time(self.radfile)
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
                log.write(self.psvfile + '\n')
                raise NonStandardExposureTimeException('Exposure time is not one of 7, 34, 404, or 5004')

        if fn is not None:
            # get the values, but skip the header
            values = [float(x.split(' ')[1].strip()) for x in open(fn).readlines() if '"' not in x]
            # get the wavelengths
            self.wavelength = [float(x.split(' ')[0].strip()) for x in open(fn).readlines() if '"' not in x]

        return values

    def update_progress(self, value=None):
        if self.main_app is not None:
            if value is not None:
                self.main_app.update_progress(value)
            else:
                self.main_app.update_progress((self.current_file / self.total_files) * 100)

    def calibrate_file(self, filename, custom_dir, out_dir):

        # check for valid rad file
        valid = self.get_rad_file(filename, out_dir)
        if valid:
            print('calibrating' + filename)
            # valid rad file, now choose values based on exp time
            try:
                values = self.choose_values(custom_dir)
                if self.total_files == 1:
                    self.update_progress(25)
                new_values = self.do_division(values)
                if self.total_files == 1:
                    self.update_progress(75)
                final_values = self.do_multiplication(new_values)
                out_filename = self.radfile.replace('RAD', 'REF')
                out_filename = out_filename.replace('rad', 'ref')
                if out_dir is not None:
                    # then save calibrated file to out dir also
                    (path, filename) = os.path.split(out_filename)
                    out_filename = os.path.join(out_dir, filename)
                write_final(out_filename, self.wavelength, final_values)
                if self.total_files == 1:
                    self.update_progress(100)
                print(filename + ' calibrated and written to ' + out_filename)
            except NonStandardExposureTimeException:
                # this file has been logged, but keep going
                pass

    def calibrate_directory(self, directory, custom_dir, out_dir):
        self.total_files = sum([len(files) for r, d, files in os.walk(directory)])
        self.current_file = 1
        for file_name in os.listdir(directory):
            full_path = os.path.join(directory, file_name)
            if ('psv' in file_name.lower() or 'rad' in file_name.lower()) and '.tab' in file_name.lower():
                self.calibrate_file(full_path, custom_dir, out_dir)
                self.current_file += 1
                self.update_progress()
            elif os.path.isdir(full_path) and full_path is not out_dir:
                self.calibrate_directory(os.path.join(directory, file_name), custom_dir, out_dir)
        self.update_progress(100)

    def calibrate_list(self, list_file, custom_dir, out_dir):
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
