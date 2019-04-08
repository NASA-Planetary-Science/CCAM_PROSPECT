import pkg
import sys
import linecache
import math as math
import numpy as np

# parsed from spectra file
ipbc = 1
ict = 1
nshots = 1
distance = 0
vnir = []
vis = []
uv = []


def readSpectra(filename):
    print(filename)

    # open file and read appropriate lines
    # ipbc:     8
    # ict:      9
    # nshots:   27
    # distance: 28
    # vnir:     80:2127
    # vis:      2228:4275
    # uv:       4376:6423
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
        vnir = np.array([float(line.rstrip('\n')) for line in f.readlines()[80:2127]])
    with open(filename, 'r') as f:
        vis = np.array([float(line.rstrip('\n')) for line in f.readlines()[2228:4275]])
    with open(filename, 'r') as f:
        uv = np.array([float(line.rstrip('\n')) for line in f.readlines()[4376:6423]])


def mean(lst):
    return sum(lst) / len(lst)


def removeOffsets():
    # VNIR: 1905 - 1920
    # VIS:  2237-2241
    # UV:   4385-4395
    global vnir, vis, uv

    vnir_off = vnir[1854:1869]
    vis_off  = vis[38:42]
    uv_off   = uv[38:48]

    vnir = np.array([v - mean(vnir_off) for v in vnir])
    vis  = np.array([v - mean(vis_off) for v in vis])
    uv   = np.array([v - mean(uv_off) for v in uv])


def getIntegrationTime():
    global ipbc, ict
    return ((ipbc*ict)/33000000) + 0.00356


def getSolidAngle():
    global distance
    return math.pi * math.pow(math.sin(math.atan(pkg.aperature/2/distance)), 2)


def getAreaOnTarget():
    global distance
    return math.pi * math.pow(pkg.fov * distance/2/10, 2)


def getRadiance(photons, t_int, fov_tgt, sa_steradian, w):
    rad = np.array([ p/t_int/fov_tgt/sa_steradian for p in photons])
    return rad / w


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Please provide the full path to the CCAM TAB file')
        exit(0)

    ccamFile = sys.argv[1]
    readSpectra(ccamFile)
    removeOffsets()
    t_int = getIntegrationTime()
    sa_steradian = getSolidAngle()
    fov_tgt = getAreaOnTarget()

    w = np.array([]) # wavelengths for vnir
    vnir_rad = getRadiance(vnir, t_int, fov_tgt, sa_steradian, w)
    w = np.array([]) # wavelengths for vis
    vis_rad = getRadiance(vis, t_int, fov_tgt, sa_steradian, w)
    w = np.array([]) # wavelengths for uv
    uv_rad = getRadiance(uv, t_int, fov_tgt, sa_steradian, w)
