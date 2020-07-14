import argparse
import os
import math as math
import numpy as np
import sys
from datetime import datetime
from ccam_prospect.utils.InputType import InputType
import ccam_prospect.utils.constant as constants
from ccam_prospect.utils.Utilities import get_integration_time, write_final, write_label, get_header_values
from ccam_prospect.utils.CustomExceptions import NonStandardHeaderException, CancelExecutionException, \
    InputFileNotFoundException


class RadianceCalibration:

    def __init__(self, log_file, main_app=None):
        # variables parsed from spectra file
        self.vnir = []
        self.vis = []
        self.uv = []
        self.headers = {}
        self.main_app = main_app
        self.total_files = 1
        self.current_file = 1
        self.header_string = ""
        self.logfile = log_file
        self.show_header_warning = True

    def get_headers(self, filename):
        """get_headers
        Just grab the first 29 lines (the header) to be copied to the calibrated rad file
        """
        with open(filename, 'r') as f:
            self.header_string = [next(f) for x in range(29)]

    def read_spectra(self, filename):
        """read_spectra
        open the response file and read the appropriate lines into
        each array of vnir, vis, and uv

            field    line

            vnir:     79:2127
            vis:      2227:4275
            uv:       4375:6423
        """
        with open(filename, 'r') as f:
            self.vnir = np.array([float(line.rstrip('\n')) for line in f.readlines()[79:2127]])
        with open(filename, 'r') as f:
            self.vis = np.array([float(line.rstrip('\n')) for line in f.readlines()[2227:4275]])
        with open(filename, 'r') as f:
            self.uv = np.array([float(line.rstrip('\n')) for line in f.readlines()[4375:6423]])

    def remove_offsets(self):
        """remove_offsets
        Find the offsets for each channel and subtract from each signal in DN
        This version uses the following lines to compute offsets
            VNIR: 1905-1920  ->   1816:1832
            VIS:  2237-2241  ->   0:5
            UV:   4385-4395  ->   0:11

        :return: the new values, with offset subtracted
        """
        # get appropriate sets of values
        vnir_off = self.vnir[1816:1832]
        vis_off = self.vis[0:5]
        uv_off = self.uv[0:11]

        # get mean of each set of values
        vnir_mean = np.mean(vnir_off)
        vis_mean = np.mean(vis_off)
        uv_mean = np.mean(uv_off)

        # subtract offset from each channel
        self.vnir = np.array([v - vnir_mean for v in self.vnir])
        self.vis = np.array([v - vis_mean for v in self.vis])
        self.uv = np.array([v - uv_mean for v in self.uv])

    def get_solid_angle(self):
        """get_solid_angle
        Calculate the solid angle subtended by the telescope aperature
        SA = pi * sin(arctan((a/2)/d))^2

        :return: the solid angle, in radians
        """
        try:
            distance = float(self.headers['distToTarget'])
        except KeyError:
            raise NonStandardHeaderException

        return math.pi * math.pow(math.sin(math.atan(constants.aperture / 2 / distance)), 2)

    def get_area_on_target(self):
        """get_area_on_target
        Calculate the associated area on the target based on the
        distance to target and angular field of view
            A = pi * (FOV * d/2)^2

        :return: the area on the target
        """
        try:
            distance = float(self.headers['distToTarget'])
        except KeyError:
            raise NonStandardHeaderException
        return math.pi * math.pow(constants.fov * distance / 2 / 10, 2)

    @staticmethod
    def get_radiance(photons, wavelengths, t_int, fov_tgt, sa_steradian):
        """get_radiance
        Calculate the radiance value of each of the spectra values in photons
        RAD = p/t/A/SA/w
        where p  = value of spectra in photons
              t  = integration time
              A  = area on the target
              SA = the solid angle subtended by the telescope aperture
              w  = the spectral bin width

        :param photons: the values for the observation, in photons
        :param wavelengths: the wavelengths corresponding to each value in photos
        :param t_int: integration time
        :param fov_tgt: the area of the FOV on the target
        :param sa_steradian: solid angle subtended by aperture in steradians
        :return: the calibrated radiance values
        """
        rad = np.array([p / t_int / fov_tgt / sa_steradian for p in photons])

        # divide each photon by the bin width (w = next wavelength - this wavelength)
        w = np.zeros(len(wavelengths))
        for iw in range(0, len(wavelengths) - 1):
            i_next = iw + 1
            w[iw] = wavelengths[i_next] - wavelengths[iw]
        w[-1] = w[-2]
        return np.divide(rad, w)

    @staticmethod
    def get_wl_and_gain(gain_file):
        """get_wl_and_response
        read the gain file to get the wavelength and response function
        (photons/DN) for each response to use to convert to units of photons

        :param gain_file: the gain file
        :return: wl, the wavelength for each response
        :return: gain, the gain for each response to get photons/DN
        """
        with open(gain_file, 'r') as f:
            wl = np.array([float(row.split()[0]) for row in f])
        with open(gain_file, 'r') as f:
            gain = np.array([float(row.split()[1]) for row in f])

        return wl, gain

    @staticmethod
    def convert_to_output_units(radiance, wavelengths):
        """convert_to_output_untis
        do the final conversion to output units

        :param radiance: the final radiance values
        :param wavelengths: wavelengths of the radiance values
        :return: the final radiance in correct output units
        """
        rad_hc = np.multiply(radiance, constants.hc)
        converted_rad = np.divide(rad_hc, np.multiply(wavelengths, 1E-9))
        return np.multiply(converted_rad, 1E7)

    @staticmethod
    def psv_to_rad(psv_file, out_dir):
        """psv_to_rad
        replace each instance of PSV with RAD.
        Also replace .txt with .tab in the case of a raw file

        :param: the original file
        """
        (path, filename) = os.path.split(psv_file)
        rad_filename = filename.replace('psv', 'rad')
        rad_filename = rad_filename.replace('PSV', 'RAD')
        rad_filename = rad_filename.replace('.TXT', '.tab')
        rad_filename = rad_filename.replace('.txt', '.tab')
        out_filename = os.path.join(path, rad_filename)

        if out_dir is not None:
            # the user specified an out_dir, so replace path with out_dir
            (path, filename) = os.path.split(out_filename)
            out_filename = os.path.join(out_dir + filename)

        return out_filename

    def update_progress(self, value=None):
        """update_progress
        update the progress bar to this value
        """
        if self.main_app is not None:
            if value is not None:
                self.main_app.update_progress(value)
            else:
                self.main_app.update_progress((self.current_file / self.total_files) * 100)

    @staticmethod
    def get_original_label(filename):
        """get_original_label
        the filename of the label for the input psv file.  should be a.lbl file """
        original_label = filename.replace('.tab', '.lbl')
        original_label = original_label.replace('.txt', '.lbl')
        original_label = original_label.replace('.TAB', '.lbl')
        original_label = original_label.replace('.TXT', '.lbl')
        return original_label

    def calibrate_file(self, ccam_file, out_dir, overwrite):
        """calibrate_file
        step through each necessary step to calibrate the file

        :param ccam_file: file to calibrate
        :param out_dir: output directory
        :param: overwrite: a boolean representing if files should be overwritten or not
        """
        # check that file exists, is a file, and is a psv *.tab or .txt file
        if os.path.exists(ccam_file) and os.path.isfile(ccam_file):
            if "psv" in ccam_file.lower() and \
                    (ccam_file.lower().endswith(".tab") or ccam_file.lower().endswith(".txt")):

                out_filename = self.psv_to_rad(ccam_file, out_dir)
                if not overwrite:
                    # if we don't want to overwrite existing files, we can skip this file if it already exists
                    if os.path.exists(out_filename) and os.path.isfile(out_filename):
                        print(out_filename + " already exists, skipping")
                        return True

                # check for original label
                original_label = self.get_original_label(ccam_file)

                self.headers = get_header_values(ccam_file)
                self.get_headers(ccam_file)

                try:
                    self.read_spectra(ccam_file)
                except ValueError:
                    with open(self.logfile, 'a+') as log:
                        print(ccam_file + ': not formatted correctly. skipping')
                        log.write(ccam_file + ': radiance calibration - file not formatted correctly \n')
                    return False

                self.remove_offsets()

                # calculate some needed values
                try:
                    t_int = get_integration_time(ccam_file)
                    sa_steradian = self.get_solid_angle()
                    fov_tgt = self.get_area_on_target()
                except NonStandardHeaderException:
                    warning = ccam_file + ': not a valid PSV file header. Skipping this file.'
                    # write to log file
                    with open(self.logfile, 'a+') as log:
                        log.write(ccam_file + ': radiance calibration - ' + warning + '\n')
                    if self.show_header_warning:
                        # show warning
                        if self.main_app is not None:
                            self.show_header_warning = self.main_app.show_warning_dialog(warning)
                    if self.show_header_warning is None:
                        # cancel
                        raise CancelExecutionException
                    # exit because file was invalid
                    return False

                if self.total_files == 1:
                    self.update_progress(25)

                # combine arrays into one ordered by wavelength
                all_spectra_dn = np.concatenate([self.uv, self.vis, self.vnir])

                # get the wavelengths and gains from gain_mars.edit
                my_path = os.path.abspath(os.path.dirname(__file__))
                gain_file = os.path.join(my_path, "constants/gain_mars.edit")
                (wavelength, gain) = self.get_wl_and_gain(gain_file)

                # multiply by the gain to get in photos
                all_spectra_photons = np.multiply(all_spectra_dn, gain)

                # calculate the radiance values
                radiance = self.get_radiance(all_spectra_photons, wavelength, t_int, fov_tgt, sa_steradian)
                if self.total_files == 1:
                    self.update_progress(50)

                # convert to units of W/m^2/sr/um from phot/sec/cm^2/sr/nm
                radiance_final = self.convert_to_output_units(radiance, wavelength)

                # rename the PSV file to RAD
                write_final(out_filename, wavelength, radiance_final, header=self.header_string)

                if os.path.exists(original_label):
                    # write new label based on original, if it exists
                    (path, filename) = os.path.split(original_label)
                    new_label_filename = filename.replace('PSV', 'RAD')
                    new_label_filename = new_label_filename.replace('psv', 'rad')
                    new_label_filename = new_label_filename.replace('lbl', 'xml')
                    (out_path, filename) = os.path.split(out_filename)
                    new_label = os.path.join(out_path, new_label_filename)
                    write_label(new_label, original_label, True)
                print(ccam_file + ' calibrated and written to ' + out_filename)
                if self.total_files == 1:
                    self.update_progress(100)
                return True
            else:
                ext = os.path.splitext(ccam_file)[1]
                if ext != '.lbl' and ext != '.LBL' and ext != '.xml' and ext != '.log':
                    # log file as long as its not a label to a psv file, and as long as its not a log file itself
                    with open(self.logfile, 'a+') as log:
                        log.write(ccam_file + ': radiance input - not a valid PSV file \n')
                return False
        else:
            raise InputFileNotFoundException(ccam_file)

    def calibrate_directory(self, directory, out_dir, overwrite):
        """calibrate_directory
        calibrate everything in this directory, recursively.

        :param: directory the directory in which to look for PSV files
        :param: out_dir the destination directory for output
        :param: overwrite a boolean representing if files should be overwritten or not
       """
        # total number of files to potentially calibrate
        self.total_files = sum([len(files) for r, d, files in os.walk(directory)])
        self.current_file = 1
        try:
            for file in os.listdir(directory):
                full_path = os.path.join(directory, file)
                if os.path.isdir(full_path) and full_path is not out_dir:
                    # recursive call for each subdirectory
                    self.calibrate_directory(os.path.join(directory, file), out_dir, overwrite)
                else:
                    self.calibrate_file(full_path, out_dir, overwrite)
                    self.current_file += 1
                    self.update_progress()
            self.update_progress(100)
        except FileNotFoundError:
            raise InputFileNotFoundException(directory)

    def calibrate_list(self, list_file, out_dir, overwrite):
        """calibrate_list
        calibrate everything in this list

        :param: list the list of psv files to calibrate
        :param: out_dir the destination directory for output
        :param: overwrite a boolean representing if files should be overwritten or not
        """
        try:
            # read each line into a list of files
            files = open(list_file).read().splitlines()
        except FileNotFoundError:
            raise InputFileNotFoundException(list_file)
        self.total_files = len(files)
        self.current_file = 1
        for file in files:
            # calibrate each file in the list
            self.calibrate_file(file, out_dir, overwrite)
            self.current_file += 1
            self.update_progress()
        self.update_progress(100)

    def calibrate_to_radiance(self, file_type, file_name, out_dir, overwrite):
        """calibrate_to_radiance
        entry point to calibrate a file, list of files, or directory

        :param: file_type either file, list of files, or directory
        :param: file_name the name of the file / directory
        :param: out_dir the destination directory for output
        :param: overwrite a boolean representing if files should be overwritten or not
        """
        if file_type.value is InputType.FILE.value:
            return self.calibrate_file(file_name, out_dir, overwrite)
        elif file_type.value is InputType.FILE_LIST.value:
            self.calibrate_list(file_name, out_dir, overwrite)
        else:
            self.calibrate_directory(file_name, out_dir, overwrite)


if __name__ == "__main__":
    # create an argument parser
    parser = argparse.ArgumentParser(description='Calibrate CCAM to Radiance')
    parser.add_argument('-f', action="store", dest='ccamFile', help="CCAM psv *.tab file")
    parser.add_argument('-d', action="store", dest='directory', help="Directory containing .tab files")
    parser.add_argument('-l', action="store", dest='list', help="File with a list of .tab files")
    parser.add_argument('-o', action="store", dest='out_dir', help="directory to store the output files")
    parser.add_argument('--no-overwrite', action="store_false", dest='overwrite', help="do not overwrite existing files")
    parser.set_defaults(overwrite=True)

    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    if args.ccamFile is not None:
        in_file_type = InputType.FILE
        in_file = args.ccamFile
    elif args.directory is not None:
        in_file_type = InputType.DIRECTORY
        in_file = args.directory
    else:
        in_file_type = InputType.FILE_LIST
        in_file = args.list

    out_dir = args.out_dir
    if out_dir is not None:
        if not out_dir.endswith('/'):
            out_dir = out_dir + '/'

    now = datetime.now()
    logfile = "badInput_{}.log".format(now.strftime("%Y%m%d.%H%M%S"))

    radianceCal = RadianceCalibration(logfile)
    radianceCal.calibrate_to_radiance(in_file_type, in_file, out_dir, args.overwrite)
