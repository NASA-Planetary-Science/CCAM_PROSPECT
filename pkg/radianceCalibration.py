import argparse
import os
import math as math
import numpy as np
import pkg.constant as cnst
import sys
from pkg.InputType import InputType
from pkg.Utilities import get_integration_time, write_final, get_header_values
from shutil import copyfile


class radianceCalibration():

    def __init__(self):
        # variables parsed from spectra file
        self.vnir = []
        self.vis = []
        self.uv = []
        self.headers = {}

    def read_spectra(self, filename):
        """read_spectra
        open the response file and read the appropriate lines into
        each array of vnir, vis, and uv, as well as info from the header

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
        distance = float(self.headers['distToTarget'])
        return math.pi * math.pow(math.sin(math.atan(cnst.aperature / 2 / distance)), 2)

    def get_area_on_target(self):
        """get_area_on_target
        Calculate the associated area on the target based on the
        distance to target and angular field of view
            A = pi * (FOV * d/2)^2

        :return: the area on the target
        """
        distance = float(self.headers['distToTarget'])
        return math.pi * math.pow(cnst.fov * distance / 2 / 10, 2)

    def get_radiance(self, photons, wavelengths, t_int, fov_tgt, sa_steradian):
        """get_radiance
        Calculate the radiance value of each of the spectra values in photons
        RAD = p/t/A/SA/w
        where p  = value of spectra in photons
              t  = integration time
              A  = area on the target
              SA = the solid angle subtended by the telescope aperature
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

    def get_wl_and_gain(self, gain_file):
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

    def convert_to_output_units(self, radiance, wavelengths):
        """convert_to_output_untis
        do the final conversion to output units

        :param radiance: the final radiance values
        :param wavelengths: wavelengths of the radiance values
        :return: the final radiance in correct output units
        """
        rad_hc = np.multiply(radiance, cnst.hc)
        converted_rad = np.divide(rad_hc, np.multiply(wavelengths, 1E-9))
        return np.multiply(converted_rad, 1E7)

    def calibrate_file(self, ccam_file, out_dir):
        """calibrate_file
        step through each necessary step to calibrate the file

        :param ccam_file: file to calibrate
        :param out_dir: output directory
        """
        if "psv" in ccam_file.lower() and ccam_file.lower().endswith(".tab"):
            self.headers = get_header_values(ccam_file)
            self.read_spectra(ccam_file)
            self.remove_offsets()
            t_int = get_integration_time(ccam_file)

            sa_steradian = self.get_solid_angle()
            fov_tgt = self.get_area_on_target()

            # combine arrays into one ordered by wavelength
            all_spectra_dn = np.concatenate([self.uv, self.vis, self.vnir])

            # get the wavelengths and gains from gain_mars.edit
            my_path = os.path.abspath(os.path.dirname(__file__))
            gain_file = os.path.join(my_path, "../constants/gain_mars.edit")
            (wavelength, gain) = self.get_wl_and_gain(gain_file)
            all_spectra_photons = np.multiply(all_spectra_dn, gain)
            radiance = self.get_radiance(all_spectra_photons, wavelength, t_int, fov_tgt, sa_steradian)

            # convert to units of W/m^2/sr/um from phot/sec/cm^2/sr/nm
            radiance_final = self.convert_to_output_units(radiance, wavelength)

            out_filename = ccam_file.replace('psv', 'rad')
            out_filename = out_filename.replace('PSV', 'RAD')
            if out_dir is not None:
                # copy original file to new out directory
                (og_path, og_filename) = os.path.split(ccam_file)
                copyfile(ccam_file, os.path.join(out_dir, og_filename))
                # then save this file to out directory
                (path, filename) = os.path.split(out_filename)
                out_filename = os.path.join(out_dir + filename)
            write_final(out_filename, wavelength, radiance_final)
            return True
        else:
            print(ccam_file + ": not a raw PSV file")
            return False

    def calibrate_directory(self, directory, out_dir):
        for file in os.listdir(directory):
            full_path = os.path.join(directory, file)
            self.calibrate_file(full_path, out_dir)
            if os.path.isdir(os.path.join(directory, file)):
                self.calibrate_directory(os.path.join(directory, file), out_dir)

    def calibrate_list(self, list_file, out_dir):
        files = open(list_file).read().splitlines()
        for file in files:
            self.calibrate_file(file, out_dir)

    def calibrate_to_radiance(self, file_type, file_name, out_dir):
        if file_type == InputType.FILE:
            self.calibrate_file(file_name, out_dir)
        elif file_type == InputType.FILE_LIST:
            self.calibrate_list(file_name, out_dir)
        else:
            self.calibrate_directory(file_name, out_dir)


if __name__ == "__main__":
    # create an argument parser
    parser = argparse.ArgumentParser(description='Calibrate CCAM to Radiance')
    parser.add_argument('-f', action="store", dest='ccamFile', help="CCAM psv *.tab file")
    parser.add_argument('-d', action="store", dest='directory', help="Directory containing .tab files")
    parser.add_argument('-l', action="store", dest='list', help="File with a list of .tab files")
    parser.add_argument('-o', action="store", dest='out_dir', help="directory to store the output files")

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

    radianceCal = radianceCalibration()
    radianceCal.calibrate_to_radiance(in_file_type, in_file, args.out_dir)
