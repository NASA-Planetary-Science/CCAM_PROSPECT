import sys



def readPSV(ccamFile):
    print(ccamFile)

    # open file and read appropriate lines
    # vnir:  51--2098
    # vis:   2199--4246
    # uv:    4347--6394

    with open(ccamFile, 'r') as f:
        vnir = [float(line.rstrip('\n')) for line in f.readlines()[80:2127]]
    with open(ccamFile, 'r') as f:
        vis = [float(line.rstrip('\n')) for line in f.readlines()[2228:4275]]
    with open(ccamFile, 'r') as f:
        uv = [float(line.rstrip('\n')) for line in f.readlines()[4376:6423]]

    return (vnir, vis, uv)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Please provide the full path to the CCAM TAB file')
        exit(0)

    aperature = 108.4;
    fov = 0.0006565;
    hc = 1.99e-25;

    ccamFile = sys.argv[1]
    data = readPSV(ccamFile)

    vnir = data[0]
    vis = data[1]
    uv = data[2]

    print("vnir ")
    print(vnir)
    print("vis  ")
    print(vis)
    print("uv   ")
    print(uv)

    