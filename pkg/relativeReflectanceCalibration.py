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


def get_rad_file(psv_file):
    global radfile, psvfile
    # get all of the values from the rad file and divide by the value_7
    radfile = psv_file.replace('psv', 'rad')
    psvfile = psv_file.replace('rad', 'psv')
    exists = os.path.isfile(radfile)
    if not exists:
        # create rad file
        calibrate_to_radiance(psv_file)


def choose_values(custom_dir, complement):
    if custom_dir is None:
        ms7 = '../sol76/cl0_404238481rad_f0050104ccam02076p1.tab'
        ms34 = '../sol76/cl0_404238492rad_f0050104ccam02076p3.tab'
        ms404 = '../sol76/cl9_404238503rad_f0050104ccam02076p3.tab'
        ms5004 = '../sol76/cl9_404238538rad_f0050104ccam02076p3.tab'
        inc7 = 24.84
        inc34 = 24.79
        inc404 = 24.75
        inc5004 = 24.61
    else:
        dirc = custom_dir

        # figure out which file is which integration time and assign to each of ms7 through ms5004
        ms7 = dirc + '/x.tab'
        ms34 = dirc + '/x.tab'
        ms404 = dirc + '/x.tab'
        ms5004 = dirc + '/x.tab'

        # get appropriate solar incidence values
        lbl = ms7.replace('tab', 'lbl').replace('rad', 'psv')
        if os.path.isfile(lbl):
            inc7 = get_incidence(lbl, complement)
            inc34 = get_incidence(ms34.replace('tab', 'lbl').replace('rad', 'psv'), complement)
            inc404 = get_incidence(ms404.replace('tab', 'lbl').replace('rad', 'psv'), complement)
            inc5004 = get_incidence(ms5004.replace('tab', 'lbl').replace('rad', 'psv'), complement)
        else:
            print("no label file found to calculate incidence values")

    # now get the values and do the cosine correction
    # get wavelengths
    # check t_int for file
    global psvfile
    t_int = get_integration_time(psvfile)
    t_int = t_int * 1000;
    values = []
    if round(t_int) == 7:
        values = [float(x.split(' ')[1].strip()) / math.cos(math.radians(inc7))
                  for x in open(ms7).readlines()]
        fn = ms7
    elif round(t_int) == 34:
        values = [float(x.split(' ')[1].strip()) / math.cos(math.radians(inc34))
                  for x in open(ms34).readlines()]
        fn = ms34
    elif round(t_int) == 404:
        values = [float(x.split(' ')[1].strip()) / math.cos(math.radians(inc404))
                  for x in open(ms404).readlines()]
        fn = ms404
    elif round(t_int) == 5004:
        values = [float(x.split(' ')[1].strip()) / math.cos(math.radians(inc5004))
                  for x in open(ms5004).readlines()]
        fn = ms5004
    else:
        print('error - integration time is not 7, 34, 404, or 5004')
        # throw an error
    global wavelength
    wavelength = [float(x.split(' ')[0].strip()) for x in open(fn).readlines()]

    return values


def get_incidence(label_file, complement):
    flag = False
    value = float('nan') # will throw an error if value not found
    with open(label_file, 'r') as infile:
        for line in infile:
            if "SOLAR_ELEVATION" in line and flag is True:
                toks = line.rsplit('=')
                value = toks[1].rstrip('<deg>\n')
                if complement:
                    value = 90 - value
                value = math.fabs(value - 37.9)
            if "SITE FRAME" in line:
                flag = True
    return value


def calibrate_file(filename, in_args):
    m = in_args.m
    global wavelength

    get_rad_file(filename)
    values = choose_values(in_args.customDir, m)
    new_values = do_division(values)
    out_filename = radfile.replace('rad', 'ref')
    write_final(out_filename, wavelength, new_values)


def calibrate_directory(directory, in_args):
    m = in_args.m
    for file in os.listdir(directory):
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
    parser.add_argument('-m', action="store_true", help="the solar incidence angle must be subtracted from 90")

    args = parser.parse_args()
    print(os.listdir('.'))
    calibrate_relative_reflectance(args)
