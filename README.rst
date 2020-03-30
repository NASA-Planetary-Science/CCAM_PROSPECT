# ccam-prospect

This software was developed as part of the NASA PDART An archive of Mars Science Laboratory ChemCam passive visible/near-infrared surface spectra. It is written in Python and can be run on any platform that has an installation of Python 3. There is both a Graphical User Interface (GUI) option and a command line option for running the tool.

This tool calibrates raw Mars Science Laboratory (MSL) Chemistry and Camera (ChemCham) passive surface spectra into radiance (240-905 nm) and relative reflectance (400-840 nm) spectra. There are default calibration files used for relative reflectance, but there is also an option for the user to select their own calibration files. For each data file that is created, a PDS4 label is also created.  The details of the calibration calculation can be found in the PDART proposal.
