# This script generates plots, plot data, and informational *.txt files given SFINCS output (*.h5) files. It can also perform basic convergence checks on the output files.
# Currently, this script cannot create 3D plots.

# Import necessary modules
from os.path import dirname, abspath, join, basename
from inspect import getfile, currentframe
import sys
import datetime
import h5py
import numpy as np
import matplotlib.pyplot as plt

thisDir = dirname(abspath(getfile(currentframe())))
sys.path.append(join(thisDir, 'src/'))
from IO import getPlotArgs, radialVarDict, adjustInputLengths, getFileInfo, makeDir, findFiles, writeFile, prettyRadialVar, prettyDataLabel, messagePrinter
from dataProc import fixOutputUnits

# Get command line arguments and radial variables
args = getPlotArgs()
radialVars = radialVarDict()
radialVar = radialVars[args.radialVar[0]]
minBound = args.radialVarBounds[0]
maxBound = args.radialVarBounds[1]

# Organize the directories that we will work in
inLists = {'sfincsDir':args.sfincsDir, 'saveLoc':args.saveLoc}
IOlists, _, _ = adjustInputLengths(inLists)

# If saveLoc was not specified, decide whether to use the profiles or equilibria locations
if all([item == None for item in IOlists['saveLoc']]):
    saveDefaultTarget = [join(item,'processed') for item in IOlists['sfincsDir']] # Give plots a subdirectory if no save locations are explicitely specified
else:
    saveDefaultTarget = IOlists['saveLoc'] 

# Specify some small functions that are useful only in this script
makeNeoclassicalNames = lambda x: [x+'_vm_'+IV for IV in IVs]
makeOtherNames = lambda x: [x+'_'+IV for IV in IVs]
now = lambda: str(datetime.datetime.now())
def writeInfoFile(listOfStrings, inputDir, outputDir, fileIDName):
    stringToWrite = ''.join(listOfStrings)
    fileToMake = join(outputDir, '{}-{}.txt'.format(inputDir, fileIDName))
    writeFile(fileToMake, stringToWrite, silent=True)

# Name some important variables
defaults = ['Delta', 'alpha', 'nu_n']

IVs = list(radialVars.values())
notRadialFluxes = ['Er', 'FSABjHat', 'FSABFlow']

[neoclassicalParticleFluxes, neoclassicalHeatFluxes, neoclassicalMomentumFluxes] = [makeNeoclassicalNames(item) for item in ['particleFlux', 'heatFlux', 'momentumFlux']]

[classicalParticleFluxes, classicalParticleFluxesNoPhi1, classicalHeatFluxes, classicalHeatFluxesNoPhi1] = [makeOtherNames(item) for item in ['classicalParticleFlux', 'classicalParticleFluxNoPhi1', 'classicalHeatFlux', 'classicalHeatFluxNoPhi1']]

nonCalcDVs = notRadialFluxes + neoclassicalParticleFluxes + neoclassicalHeatFluxes + neoclassicalMomentumFluxes + classicalParticleFluxes + classicalParticleFluxesNoPhi1 + classicalHeatFluxes + classicalHeatFluxesNoPhi1

extras = ['Zs']

# Name some other variables to be calculated later
[totalParticleFluxes, totalHeatFluxes] = [makeOtherNames(item) for item in ['totalParticleFlux', 'totalHeatFlux']]

radialCurrents = makeNeoclassicalNames('radialCurrent')

DVs = nonCalcDVs + totalParticleFluxes + totalHeatFluxes + radialCurrents

# Loop through each directory
allData = {}
didNotConvergeAll = []
didNotConvergeDir = []
for i,unRegDirectory in enumerate(IOlists['sfincsDir']):
    
    # Regularize input directory name
    _, _, _, directory, _ = getFileInfo('/arbitrary/path', unRegDirectory, 'arbitrary')

    # Make target directory if it does not exist
    outDir = makeDir(saveDefaultTarget[i]) # Note that this script has file overwrite powers!
    
    # Retrieve the data
    dataFiles = findFiles('sfincsOutput.h5', directory) # Note that sfincsScan breaks if you use a different output file name, so the default is hard-coded in

    if len(dataFiles) == 0:
        raise IOError('No SFINCS output (*.h5) file could be found in the input directory {}.'.format(directory))

    # FIXME kill this commented code if you can
    '''
    # Sort out the SFINCS subdirectories 
    #subdirs = [item.replace(directory+'/','') for item in dataFiles]

    #splitSubdirs = [item.split('/') for item in subdirs]

    #dataDepth = len(splitSubdirs[0])

    #if not all([len(item) == dataDepth for item in splitSubdirs]):
        #raise IOError('The structure of the SFINCS directory {} does not seem to be normal.'.format(directory))
    '''

    # Cycle through each file, read its data, and put that data in the proper place
    radDirName = None
    loadedData = {}
    for j,file in enumerate(dataFiles): # Scans through radial directories, and Er directories if present

        subdir = file.replace(directory+'/','') #FIXME this code should allow you to plot SFINCS directories with some scanType4 and some scanType5 runs... check!
        subdictNames = subdir.split('/')
        dataDepth = len(subdictNames)

        # Open the output file and do a basic (not 100% conclusive) convergence check before reading its data
        dirOfFileName = dirname(file)

        try:
            f = h5py.File(file, 'r')
            _ = f['finished'][()]
            shouldBePresent = f['FSABFlow'][()]
            if any(np.isnan(shouldBePresent)):
                raise ValueError
            convergenceState = 'PASS'
        
        except (IOError, KeyError, ValueError):
            didNotConvergeAll.append(file)
            didNotConvergeDir.append(file)
            convergenceState = 'FAIL'

        convergenceStringList = [now() + '\n']
        convergenceStringList.append('This run {}ED basic convergence tests.\n'.format(convergenceState))
        writeInfoFile(convergenceStringList, basename(dirOfFileName), dirOfFileName, 'convergence')
        
        if args.checkConv or convergenceState == 'FAIL':
            continue

        # Read the desired data from the file
        for varName in defaults + IVs + nonCalcDVs + extras:
            loadedData[varName] = f[varName][()]

        # Check that the default parameters are in order
        if loadedData['Delta'] != 0.0045694 or loadedData['alpha'] != 1 or loadedData['nu_n'] != 0.00833:
            raise IOError('It appears that the values of Delta, alpha, or nu_n were changed from their defaults. Please use the defaults to make unit conversions simpler.')

        # Calculate other desired quantities
        for radInd,(totalParticleFlux, totalHeatFlux) in enumerate(zip(totalParticleFluxes, totalHeatFluxes)):
            loadedData[totalParticleFlux] = loadedData[neoclassicalParticleFluxes[radInd]] + loadedData[classicalParticleFluxes[radInd]]
            loadedData[totalHeatFlux] = loadedData[neoclassicalHeatFluxes[radInd]] + loadedData[classicalHeatFluxes[radInd]]

        for radInd,radialCurrent in enumerate(radialCurrents):
           loadedData[radialCurrent] = np.dot(loadedData['Zs'], loadedData[neoclassicalParticleFluxes[radInd]])

        # Put the data in the appropriate place
        if dataDepth == 2: # Only radial directories are present
            allData[subdictNames[0]] = loadedData
        
        elif dataDepth == 3: # Radial and Er directories are present

            if radDirName != subdictNames[0]: # You are in a different radial directory from the last iteration over dataFiles
                if j != 0: # We shouldn't try to append data on the first loop iteration
                    allData[radDirName] = radData
                radDirName = subdictNames[0]
                radData = {}
            
            radData[subdictNames[1]] = loadedData
        
        else:
            raise IOError('The structure of the SFINCS directory {} does not seem to be normal.'.format(directory))

        loadedData = {} # This should be clean for each new file

    if not args.checkConv and len(didNotConvergeDir) != len(dataFiles):
    
        # Now sort out what to plot
        stuffToPlot = {}
        for key,val in allData.items():
            
            if dataDepth == 2: # Only radial directories are present
                radialVal = val[radialVar]
            else: # Radial and Er directories are present
                radialVal = val[list(val.keys())[0]][radialVar] # Note that the same flux surface is used for each electric field sub-run
            
            minPass = minBound < 0 or minBound <= radialVal
            maxPass = maxBound < 0 or maxBound >= radialVal

            if minPass and maxPass:
                stuffToPlot[key] = val

        # Actually plot things
        nameOfDir = basename(directory)

        ErChoices = []
        IVvec = []
        for IV in IVs: # Select the radial variable you're plotting against
            
            DVvec = []
            for DV in DVs: # Select the data you want to plot

                if 'Flux' in DV and DV[0] not in ['c','t']: # If DV is a neoclassical flux #FIXME test this
                    DVnameForPlot = 'neoclassical' + DV[0].upper() + DV[1:]
                else:
                    DVnameForPlot = DV
                
                baseName = nameOfDir + '-' + DVnameForPlot + '-vs-' + IV 
                plotName = baseName + '.pdf'
                dataName = baseName + '.dat'
                Zsname = baseName + '.Zs'

                fullPlotPath = join(outDir, plotName)
                fullDataPath = join(outDir, dataName)
                fullZsPath = join(outDir, Zsname)
        
                for radKey,radData in stuffToPlot.items():

                    if dataDepth == 2: # Only radial directories are present
                        dataToUse = radData

                    else: # Radial and Er directories are present
                        convergedErAbsVals = dict([(ErKey, np.abs(ErData['Er'])) for ErKey, ErData in radData.items()])
                        minErKey = min(convergedErAbsVals) # Returns key of Er subdirectory that has the smallest |Er| 
                        # If there are multiple minima, only the key of the first minimum will be returned.
                        # This should be fine - one would expect SFINCS runs with matching |Er| values to have converged to the same answer.
                        dataToUse = radData[minErKey]
                        ErChoices.append(join(radKey, minErKey) + '\n')
                   
                    IVvec.append(dataToUse[IV])
                    DVvec.append(fixOutputUnits(DV, dataToUse[DV]))

                IVvec = np.array(IVvec)
                DVvec = np.array(DVvec)
                
                DVshape = DVvec.shape
                if DVshape[-1] == 1: # Indicates that floats are being stores as single-element lists
                    DVvec = DVvec.reshape(DVshape[:-1]) # Gets rid of those extra lists so floats behave like floats

                combined = np.column_stack((IVvec,DVvec)) # The IV values will be the first column. The data comes in subsequent columns.
                combined = combined[combined[:, 0].argsort()] # This sorts the data so that radVar values are strictly ascending

                np.savetxt(fullDataPath, combined)

                plt.figure()
                plt.plot(combined[:,0], combined[:,1:]) # One horizontal axis data vector, (possibly) multiple vertical axis data vectors
                plt.xlabel(prettyRadialVar(IV))
                plt.ylabel(prettyDataLabel(DV))
                
                numLines = combined.shape[1] - 1
                
                if numLines > 1:
                    
                    Zs = dataToUse['Zs'] # Note that this assumes the Z for each species is the same throughout the plasma (i.e. the amount of stripping is constant)

                    np.savetxt(fullZsPath, Zs)
                    
                    leg = []
                    for specNum in range(numLines):
                        leg.append(r'$Z={}$'.format(int(Zs[specNum])))

                    plt.legend(leg, loc='best')

                plt.xlim(xmin=0)
                plt.margins(0.01)
                
                plt.savefig(fullPlotPath, bbox_inches='tight', dpi=400)
                plt.close('all')

                IVvec = []
                DVvec = []
        
        if len(didNotConvergeDir) > 0: # Note that if every output in an input directory did not converge, this file will not be written
            formattedList = [item + '\n' for item in didNotConvergeDir]
            formattedList.insert(0, now() + '\n') # FIXME ensure this works
            writeInfoFile(formattedList, nameOfDir, outDir, 'didNotConverge')

        if len(ErChoices) > 0:
            uniqueChoices = list(set(ErChoices))
            uniqueChoices.sort()
            uniqueChoices.insert(0, now() + '\n') # FIXME ensure this works
            writeInfoFile(uniqueChoices, nameOfDir, outDir, 'ErChoices')
        
        allData = {} # This should be clean for each new directory
        didNotConvergeDir = [] # This should be clean for each new directory
        messagePrinter('Finished processing all available data in {}.'.format(directory))

# Notify the user of convergence issues if necessary
if len(didNotConvergeAll) > 0:
    messagePrinter('It appears that the SFINCS run(s) which created the output file(s) in the list below did not complete/converge properly.')
    print(didNotConvergeAll)
