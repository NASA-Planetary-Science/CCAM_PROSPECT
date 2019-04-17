import pkg
import sys
import linecache
import math as math
import numpy as np

# variables parsed from spectra file
ipbc = 1
ict = 1
nshots = 1
distance = 0
vnir = []
vis = []
uv = []


def read_spectra(filename):
    """read_spectra
    open the response file and read the appropriate lines into
    each array of vnir, vis, and uv, as well as info from the header

        field    line

        ipbc:     8
        ict:      9
        nshots:   27
        distance: 28
        vnir:     79:2127
        vis:      2227:4275
        uv:       4375:6423
    """


    global ipbc, ict, nshots, distance, vnir, vis, uv

    line = linecache.getline(filename, 8)
    ipbc = float(line.rsplit(":")[1].rstrip('"\n'))
    line = linecache.getline(filename, 9)
    ict = float(line.rsplit(":")[1].rstrip('"\n'))
    line = linecache.getline(filename, 27)
    nshots = int(line.rsplit(":")[1].rstrip('"\n'))
    line = linecache.getline(filename, 28)
    distance = float(line.rsplit(":")[1].rstrip('"\n'))

    with open(filename, 'r') as f:
        vnir = np.array([float(line.rstrip('\n')) for line in f.readlines()[79:2127]])
    with open(filename, 'r') as f:
        vis = np.array([float(line.rstrip('\n')) for line in f.readlines()[2227:4275]])
    with open(filename, 'r') as f:
        uv = np.array([float(line.rstrip('\n')) for line in f.readlines()[4375:6423]])


def remove_offsets():
    """remove_offsets
    Find the offsets for each channel and subtract from each singal in DN
    This version uses the following lines to compute offsets
        VNIR: 1905-1920  ->   1816:1832
        VIS:  2237-2241  ->   0:5
        UV:   4385-4395  ->   0:11

    :return: the new values, with offset subtracted
    """
    global vnir, vis, uv

    # get appropriate sets of values
    vnir_off = vnir[1816:1832]
    vis_off = vis[0:5]
    uv_off = uv[0:11]

    # get mean of each set of values
    vnir_mean = np.mean(vnir_off)
    vis_mean = np.mean(vis_off)
    uv_mean = np.mean(uv_off)

    # subtract offset from each channel
    vnir = np.array([v - vnir_mean for v in vnir])
    vis = np.array([v - vis_mean for v in vis])
    uv = np.array([v - uv_mean for v in uv])


def get_integration_time():
    """get_integration_time
    Calculate the integration time based on values in the header

    :return: integration time
    """
    global ipbc, ict
    return ((ipbc * ict) / 33000000) + 0.00356


def get_solid_angle():
    """get_solid_angle
    Calculate the solid angle subtended by the telescope aperature
    SA = pi * sin(arctan((a/2)/d))^2

    :return: the solid angle, in radians
    """
    global distance
    return math.pi * math.pow(math.sin(math.atan(pkg.aperature / 2 / distance)), 2)


def get_area_on_target():
    """get_area_on_target
    Calculate the associated area on the target based on the
    distance to target and angular field of view
    TODO We divide the distance by 10 because why?
        A = pi * (FOV * d/2)^2

    :return: the area on the target
    """
    global distance
    return math.pi * math.pow(pkg.fov * distance / 2 / 10, 2)


def get_radiance(photons, wavelengths):
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
    :return: the calibrated radiance values
    """
    rad = np.array([p / t_int / fov_tgt / sa_steradian for p in photons])

    # divide each photon by the bin width (w = next wavelength - this wavelength)
    w = np.zeros(len(wavelengths))
    for iw in range(0, len(wavelengths) - 1):
        inext = iw + 1
        w[iw] = wavelengths[inext] - wavelengths[iw]
    w[-1] = w[-2]  # TODO what to use as last bin width?
    return np.divide(rad, w)


def get_wl_and_response(gain_file):
    """get_wl_and_response
    read the gain file to get the wavelength and response function
    (photons/DN) for each response to use to convert to units of photons

    :return: wl, the wavelength for each response
    :return: gain, the gain for each response to get photons/DN
    """
    with open(gain_file, 'r') as f:
        wl = np.array([float(row.split()[0]) for row in f])
    with open(gain_file, 'r') as f:
        gain = np.array([float(row.split()[1]) for row in f])

    return wl, gain


def convert_to_output_units(radiance, wavelengths):
    rad_hc = np.multiply(radiance, pkg.hc)
    converted_rad = np.divide(rad_hc, np.multiply(wavelengths, 1E-9))
    return np.multiply(converted_rad, 1E7)


def write_final(file_to_write, wavelengths, radiance_final):
    with open(file_to_write, 'w') as f:
        for ii in range(0, len(wavelengths)):
            f.write('%3.3f %3.5f\n' % (wavelengths[ii], radiance_final[ii]))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Please provide the full path to the CCAM TAB file')
        exit(0)

    ccamFile = sys.argv[1]
    read_spectra(ccamFile)
    remove_offsets()
    print(vnir)
    t_int = get_integration_time()
    sa_steradian = get_solid_angle()
    fov_tgt = get_area_on_target()

    # combine arrays into one ordered by wavelength
    allSpectra_DN = np.concatenate([uv, vis, vnir])

    # TODO what to do with this gain_mars.edit file
    (wavelength, response) = get_wl_and_response('/Users/osheacm1/Documents/SAA/PDART/OldCode/gain_mars.edit')
    allSpectra_photons = np.multiply(allSpectra_DN, response)
    radiance = get_radiance(allSpectra_photons, wavelength)

    # convert to units of W/m^2/sr/um from phot/sec/cm^2/sr/nm
    radiance_final = convert_to_output_units(radiance, wavelength)

    outfilename = ccamFile.replace('psv', 'rad')
    print(outfilename)
    write_final(outfilename, wavelength, radiance_final)