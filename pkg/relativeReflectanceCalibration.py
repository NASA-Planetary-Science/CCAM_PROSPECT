import pkg
import sys
import linecache
import math as math
import numpy as np


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Please provide the full path to the CCAM TAB file')
        exit(0)
    baseDir = 'Users/osheacm1/Documents/SAA/PDART/oldCode/target11sol76/'
    ms7    = baseDir + 'CL0_404238481PSV_F0050104CCAM02076P1.TXT.RAD.cor.7ms.txt.cos'
    ms34   = baseDir + 'CL0_404238492PSV_F0050104CCAM02076P1.TXT.RAD.cor.34ms.txt.cos'
    ms404  = baseDir + 'CL9_404238503PSV_F0050104CCAM02076P1.TXT.RAD.cor.404ms.txt.cos'
    ms5004 = baseDir + 'CL9_404238538PSV_F0050104CCAM02076P1.TXT.RAD.cor.5004ms.txt.cos'