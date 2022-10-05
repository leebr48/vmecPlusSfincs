# This script reads profile data from the BEAMS3D section of the STELLOPT namelist and converts it to SFINCS-readable profiles. FIXME description when finished

# Import necessary packages
import argparse
import os
import numpy as np
from IO import listifyBEAMS3DFile, extractDataList, makeProfileNames, generatePreamble
from dataProc import scaleData, nonlinearInterp

# Specify and explain command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--inFile', type=str, nargs=1, required=True, help='Input file name, with path if necessary.')
parser.add_argument('--outFileName', type=str, nargs=1, required=False, default=None, help='Output file suffix (profile.<outFileName>). Defaults to suffix of input file.')
parser.add_argument('--saveLoc', type=str, nargs=1, required=False, default=None, help='Location in which to save profile.<outFileName>. Defaults to <inFile> location.')
parser.add_argument('--minRad', type=float, nargs=1, required=False, default=0.05, help='Minimum value of the generalized radial coordinate for the scan.')
parser.add_argument('--maxRad', type=float, nargs=1, required=False, default=0.95, help='Maximum value of the generalized radial coordinate for the scan.')
parser.add_argument('--numRad', type=float, nargs=1, required=False, default=16, help='Number of radial surfaces on which to perform the scan.')
parser.add_argument('--noEr', action='store_true', required=False, help='Ignore the scan over the radial electric field.')
parser.add_argument('--phiBar', type=float, nargs=1, required=False, default=1, help='Reference electrostatic potential in units of kV.')
parser.add_argument('--nBar', type=float, nargs=1, required=False, default=1e20, help='Reference density in units of m^(-3). Note that Python "E" notation is equivalent to Fortran "D" notation.')
parser.add_argument('--TBar', type=float, nargs=1, required=False, default=1, help='Reference temperature in units of keV.')
args = parser.parse_args()

# Name input and output files
inFile = os.path.abspath(args.inFile[0])
inFileName = inFile.split('/')[-1]
filesSuffix = inFileName.replace('input.','')
inFilePath = inFile.replace(inFileName,'')

if args.saveLoc == None:
    outFilePath = inFilePath
else:
    outFilePath = os.path.abspath(args.saveLoc[0])

if args.outFileName == None:
    outFileName = 'profile.' + filesSuffix
else:
    outFileName = 'profile.' + args.outFileName[0]

outFile = outFilePath + '/' + outFileName

# Extract the data from the BEAMS3D file and scale it.
listifiedInFile = listifyBEAMS3DFile(inFile)

prefixesOfInterest = ['NE', 'TI', 'NE', 'TE'] # Note that the order must match the column order of the profiles.xxx file! Repeated prefixes are fine. #FIXME how deal with ZEFF and POT? #FIXME this list could/should probably be an input. It should also be strip()'ed and lower()'ed right off the bat, if it isn't already. (Doing that immediately would probably help for later.)

if args.noEr:
    for item in prefixesOfInterest:
        if item.lower() == 'pot':
            raise IOError('If you are not calculating the electric field, you should not specify the potential.')

varsOfInterest = makeProfileNames(prefixesOfInterest)
dataOfInterest = extractDataList(listifiedInFile, varsOfInterest)

# Scale the data according to the reference variable values.
scaledData = scaleData(dataOfInterest, args.phiBar, args.nBar, args.TBar)

# Interpolate the data in case the radial lists do not all contain the same points.
interpolatedData = nonlinearInterp(scaledData)

# Gather the components of the profile.xxx file
radial_coordinate_ID = 1 # Corresponds to normalized toroidal flux, which is the VMEC S. #FIXME move to top of file, or make an input?

radii = np.linspace(start=args.minRad, stop=args.maxRad, num=args.numRad, endpoint=True)

if args.noEr:
    NErs = lambda x: 0
    generalEr_min = lambda x: 0
    generalEr_max = lambda x: 0
    # Note that these quantities only must be specified for scanType = 5. They are ignored if scanType = 4.
else:
    raise AssertionError('FIXME: I cannot handle radial electric fields yet!')

stringToWrite = generatePreamble(radial_coordinate_ID)

partString = ''
