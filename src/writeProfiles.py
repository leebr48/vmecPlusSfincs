# This script creates a SFINCS-readable profiles file.

def run(profilesInUse, saveLocUse):

    '''
    The inputs are set by a wrapper script.
    '''

    # Import necessary modules
    import numpy as np
    from os.path import join
    from matplotlib.pyplot import subplots
    from IO import getArgs, getFileInfo, cleanStrings, listifyBEAMS3DFile, extractDataList, makeProfileNames, generatePreamble, generateDataText, writeFile
    from dataProc import findMinMax, scaleData, nonlinearInterp

    # Get command line arguments
    args = getArgs()

    # Name input and output files
    inFile, _, _, outDir, outFile = getFileInfo(profilesInUse, saveLocUse, 'profiles') # Name mandated by SFINCS
    
    plotName = 'interpFuncFit'
    plotFile = join(outDir, plotName+'.pdf')

    # Clean input variable names and do some clerical checks
    prefixesOfInterest = cleanStrings(args.vars)

    # Extract the data from the BEAMS3D input file
    listifiedInFile = listifyBEAMS3DFile(inFile)

    varsOfInterest = makeProfileNames(prefixesOfInterest)
    dataOfInterest = extractDataList(listifiedInFile, varsOfInterest)

    radialBounds = findMinMax(dataOfInterest)

    # Scale the data according to the reference variable values
    scaledData = scaleData(dataOfInterest)
    
    # Interpolate the data in case the radial lists do not all contain the same points
    ders = {}
    for key,val in scaledData.items():
        ders[key] = 0

    interpolatedData = nonlinearInterp(scaledData, ders)

    # Gather the components of profiles file
    radial_coordinate_ID = 1 # Corresponds to normalized toroidal flux, which is S in STELLOPT and psiN in SFINCS

    radii = list(np.linspace(start=radialBounds['min'], stop=radialBounds['max'], num=args.numInterpSurf[0], endpoint=True))

    # Note that NErs, generalEr_min, and generalEr_max are only used by SFINCS if scanType = 5.
    NErs = lambda x: args.numManErScan[0]
    generalEr_min = lambda x: args.minEr[0]
    generalEr_max = lambda x: args.maxEr[0]

    funcs = [NErs, generalEr_min, generalEr_max]

    funcs.extend([interpolatedData[prefix] for prefix in prefixesOfInterest])

    # Plot the fitted interpolation functions to ensure they represent the data well
    fig,ax = subplots()

    leg = []
    for key, data in scaledData.items():
        ax.scatter(data['iv'], data['dv'])
        ax.plot(radii, interpolatedData[key](radii))
        leg.append(key)

    ax.legend(leg, loc='best')
    ax.set_xlabel(r'SFINCS $\psi_{N}$ $\left(= \mathrm{STELLOPT}{\ }S\right)$')
    ax.set_ylabel('Normalized Value')

    fig.savefig(plotFile, bbox_inches='tight', dpi=400)
    print('{} plot created.'.format(plotName))

    # Get the string to write in profiles file
    stringToWrite = generatePreamble(radial_coordinate_ID)
    stringToWrite += generateDataText(radii, *funcs)

    # Write profiles file
    writeFile(outFile, stringToWrite)
