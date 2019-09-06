import math as math
import numpy as np
import os
import argparse
from Utilities import get_integration_time, write_final
from radianceCalibration import calibrate_to_radiance

psvfile = ''
radfile = ''
wavelength = []


def do_division(values):
    '''
    Divide each value in the file by the calibration values
    :param values:
    :return:
    '''
    global radfile
    values_orig = [float(x.split(' ')[1].strip()) for x in open(radfile).readlines()]

    # divide original values by the appropriate calibration values
    # to get relative reflectance.  If divide by 0, just = 0
    with np.errstate(divide='ignore', invalid='ignore'):
        c = np.true_divide(values_orig, values)
        c[c == np.inf] = 0
        c = np.nan_to_num(c)

    return c


def do_multiplication(values):
    '''
    Multiply each value in the file by the lab bidirectional spectrum value
    :param values:
    :return:
    '''
    conv = '../sol76/Target11_60_95.txt.conv';
    values_conv = [float(x.split()[1].strip()) for x in open(conv).readlines()]

    # multiply original values by the appropriate calibration values
    # to get relative reflectance.
    c = np.multiply(values_conv, values)

    return c


def get_rad_file(psv_file):
    global radfile, psvfile
    # get all of the values from the rad file and divide by the value_7
    radfile = psv_file.replace('psv', 'rad')
    psvfile = psv_file.replace('rad', 'psv')
    exists = os.path.isfile(radfile)
    if not exists:
        # create rad file
        calibrate_to_radiance(psv_file)


def choose_values(custom_dir):
    if custom_dir is None:
        ms7 = '../sol76/cl0_404238481cor_f0050104ccam02076p1.tab'
        ms34 = '../sol76/cl0_404238492cor_f0050104ccam02076p3.tab'
        ms404 = '../sol76/cl9_404238503cor_f0050104ccam02076p3.tab'
        ms5004 = '../sol76/cl9_404238538cor_f0050104ccam02076p3.tab'
    else:
        dirc = custom_dir
        # TODO add functionality for custom files

    # now get the cosine-corrected values from the correct file
    # check t_int for file
    global psvfile
    t_int = get_integration_time(psvfile)
    t_int = t_int * 1000;
    values = []
    if round(t_int) == 7:
        values = [float(x.split(' ')[1].strip()) for x in open(ms7).readlines()]
        fn = ms7
    elif round(t_int) == 34:
        values = [float(x.split(' ')[1].strip()) for x in open(ms34).readlines()]
        fn = ms34
    elif round(t_int) == 404:
        values = [float(x.split(' ')[1].strip()) for x in open(ms404).readlines()]
        fn = ms404
    elif round(t_int) == 5004:
        values = [float(x.split(' ')[1].strip()) for x in open(ms5004).readlines()]
        fn = ms5004
    else:
        print('error - integration time is not 7, 34, 404, or 5004')
        # throw an error
    # get the wavelengths
    global wavelength
    wavelength = [float(x.split(' ')[0].strip()) for x in open(fn).readlines()]

    return values


def calibrate_file(filename, in_args):
    global wavelength

    get_rad_file(filename)
    values = choose_values(in_args.customDir)
    new_values = do_division(values)
    final_values = do_multiplication(new_values)
    out_filename = radfile.replace('RAD', 'REF')
    out_filename = out_filename.replace('rad', 'ref')
    write_final(out_filename, wavelength, final_values)


def calibrate_directory(directory, in_args):
    for file in os.listdir(directory):
        if 'psv' in file.lower() and '.tab' in file.lower():
            full_path = directory + file
            calibrate_file(full_path, in_args)


def calibrate_list(listfile, in_args):
    files = open(listfile).read().splitlines()
    for file in files:
        calibrate_file(file, in_args)


def calibrate_relative_reflectance(in_args):
    # figure out if this is a file, dir, or list of files
    if in_args.ccamFile is not None:
        calibrate_file(args.ccamFile, in_args)
    if in_args.directory is not None:
        calibrate_directory(args.directory, in_args)
    if in_args.list is not None:
        calibrate_list(args.list, in_args)


if __name__ == "__main__":

    # create a command line parser
    parser = argparse.ArgumentParser(description='Relative Reflectance Calibration')
    parser.add_argument('-f', action="store", dest='ccamFile', help="CCAM psv or rad *.tab file")
    parser.add_argument('-d', action="store", dest='directory', help="Directory containing .tab files to calibrate")
    parser.add_argument('-l', action="store", dest='list', help="File with a list of .tab files to calibrate")
    parser.add_argument('-c', action="store", dest='customDir', help="directory containing custom calibration files")

    args = parser.parse_args()
    print(os.listdir('.'))
    calibrate_relative_reflectance(args)
