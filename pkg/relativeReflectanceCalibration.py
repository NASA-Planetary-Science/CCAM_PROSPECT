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
    :param radFile:
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


def choose_values(customDir):
    m = False
    if customDir is None:
       '''
      If the user wants to use the default, we use sol76 data.
      These default files are in pkg/sol76.
      we set m to true because we need to do the 90-incidence correction
       '''
       m = True

       ms7 = 'sol76/cl0_404238481rad_f0050104ccam02076p1.tab'
       ms34 = 'sol76/cl0_404238492rad_f0050104ccam02076p3.tab'
       ms404 = 'sol76/cl9_404238503rad_f0050104ccam02076p3.tab'
       ms5004 = 'sol76/cl9_404238538rad_f0050104ccam02076p3.tab'
       inc7 = 24.84
       inc34 = 24.79
       inc404 = 24.75
       inc5004 = 24.61
    else:
       dirc = customDir

       # figure out which file is which integration time and assign to each of ms7 through ms5004
       ms7 = dirc + '/x.tab'
       ms34 = dirc + '/x.tab'
       ms404 = dirc + '/x.tab'
       ms5004 = dirc + '/x.tab'

       # get appropriate solar incidence values
       lbl = ms7.replace('tab', 'lbl').replace('rad', 'psv')
       ifile = os.path.isfile(lbl)
       inc7 = get_incidence(lbl, m)
       inc34 = get_incidence(ms34.replace('tab', 'lbl').replace('rad', 'psv'), m)
       inc404 = get_incidence(ms404.replace('tab', 'lbl').replace('rad', 'psv'), m)
       inc5004 = get_incidence(ms5004.replace('tab', 'lbl').replace('rad', 'psv'), m)

    # now get the values and do the cosine correction
    # get wavelengths
    # check t_int for file
    global psvfile
    t_int = get_integration_time(psvfile)
    t_int = t_int * 1000;
    values = []
    if round(t_int) == 7:
       values = [float(x.split(' ')[1].strip()) / math.cos(inc7)
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


def get_incidence(labelfile, complement):
    flag = False
    value = float('nan') # will throw an error if value not found
    with open(labelfile, 'r') as infile:
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


def calibrate_file(filename, input):
    m = input.m
    global wavelength

    get_rad_file(filename)
    values = choose_values(input.customDir)
    newValues = do_division(values)
    outfilename = radfile.replace('rad', 'ref')
    write_final(outfilename, wavelength, newValues)


def calibrate_directory(dir, input):
    x=2


def calibrate_list(listfile, input):
    x=3


def calibrate_relative_reflectance(input):
    # figure out if this is a file, dir, or list of files
    if input.ccamFile is not None:
        calibrate_file(args.ccamFile, input)
    if input.directory is not None:
        calibrate_directory(args.directory, input)
    if input.list is not None:
        calibrate_list(args.list, input)


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
