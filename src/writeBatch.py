# This script creates a job.sfincsScan batch script.

def run():
    
    # Import necessary modules
    from os import environ
    from IO import getArgs, getFileInfo, writeFile

    # Get command line arguments
    args = getArgs()

    # Name output file
    _, _, _, _, outFile = getFileInfo(args.profilesIn[0], args.saveLoc[0], 'job.sfincsScan')

    # Load the email address to notify of job developments
    email = environ['SFINCS_BATCH_EMAIL']

    # Load the location of the SFINCS directory
    sfincsLoc = environ['SFINCS_PATH'] + '/fortran/version3/sfincs'

    # Load the machine name
    machineVar = 'MACHINE'
    machine = environ[machineVar]

    # Create the string to be written
    stringToWrite = '#!/bin/bash -l\n'
    stringToWrite += '# Standard output and error:\n'
    stringToWrite += '#SBATCH -o ./sfincsJob.out.%j\n'
    stringToWrite += '#SBATCH -e ./sfincsJob.err.%j\n'
    stringToWrite += '# Initial working directory:\n'
    stringToWrite += '#SBATCH -D ./\n'
    stringToWrite += '# Job Name:\n'
    stringToWrite += '#SBATCH -J sfincs\n'
    stringToWrite += '#\n'
    stringToWrite += '# Number of MPI Tasks:\n'
    stringToWrite += '#SBATCH --ntasks={}\n'.format(args.nTasks[0])
    stringToWrite += '# Memory allocation (MB) of the job:\n'
    stringToWrite += '#SBATCH --mem={}\n'.format(args.mem[0])
    stringToWrite += '#\n'
    if args.notifs[0] == 'bad':
        stringToWrite += '#SBATCH --mail-type=fail,invalid_depend,requeue,stage_out\n'
    elif args.notifs[0] == 'all':
        stringToWrite += '#SBATCH --mail-type=all\n'
    elif args.notifs[0] == 'none':
        stringToWrite += '#SBATCH --mail-type=none\n'
    stringToWrite += '#SBATCH --mail-user={}\n'.format(email)
    stringToWrite += '#\n'
    stringToWrite += '# Wall clock limit:\n'
    stringToWrite += '#SBATCH --time={}\n'.format(args.time[0].strip())
    stringToWrite += '\n'
    stringToWrite += '# Load necessary modules (typically must be the same as those used for compiling the code):\n'
    stringToWrite += 'module purge\n'

    if machine == 'raven' or machine == 'cobra':
        stringToWrite += 'module load git\n'
        stringToWrite += 'module load intel/19.1.2\n'
        stringToWrite += 'module load mkl\n'
        stringToWrite += 'module load impi/2019.8\n'
        stringToWrite += 'module load hdf5-mpi/1.10.6\n'
        stringToWrite += 'module load netcdf-mpi/4.7.0\n'
        stringToWrite += 'module load fftw-mpi\n'
        stringToWrite += 'module load anaconda/3/2020.02\n'
        stringToWrite += 'module load petsc-real/3.13.5\n'
        stringToWrite += 'module load mumps-32-noomp/5.1.2\n'
        stringToWrite += 'module load netcdf-mpi/4.7.0\n'
        stringToWrite += '\n'
    else:
        from os.path import abspath
        from inspect import getfile, currentframe
        thisFile = abspath(getfile(currentframe()))
        _, thisFileName, _, _, _ = getFileInfo(thisFile, 'arbitrary/path', 'arbitrary')
        errString = 'This machine (as identified by the "{}" environment variable)'.format(machineVar)
        errString += ' is not recognized. Please add the necessary "module load" commands to {}.'.format(thisFileName)
        raise OSError(errString)

    stringToWrite += '# Run the program:\n'
    stringToWrite += 'srun {} -ksp_view\n'.format(sfincsLoc)

    # Write job.sfincsScan file
    writeFile(outFile, stringToWrite)
