"""
Created by:      Bryce Chung
Last modified:   January 4, 2016

Description:     This class allows the user to run AnimatLab simulations from Python.
"""

# Import dependencies
import os, glob, shutil

from copy import copy

import subprocess
import multiprocessing

global verbose
verbose = 3

## ===== ===== ===== ===== =====
## ===== ===== ===== ===== =====

class AnimatLabSimRunnerError(Exception):
    """
    This class manages animatLabSimulationRunner errors.
    Right now this class does nothing other than print an error message.
    
    Last updated:   January 4, 2016
    Modified by:    Bryce Chung
    """
    
    def __init__(self, value):
        """
        __init__(value)
        Set the value of the error message.
        """
        
        self.value = value
        
    def __str__(self):
        """
        __str__()
        Returns the value of the error message.
        """
        
        return repr(self.value)
        
def runAnimatLabSimulationWrapper(args):
    return runAnimatLabSimulation(*args)


def runAnimatLabSimulation(fldrCount, asimFile, obj_simRunner):
    
    if verbose > 1:
        print "\n\nPROCESSING SIMULATION FILE: %s" % asimFile
    
    # Make a copy of common model files to use during simulations
    fldrActiveFiles = os.path.join(obj_simRunner.rootFolder, obj_simRunner.name+'-'+str(fldrCount))
    shutil.copytree(obj_simRunner.commonFiles, fldrActiveFiles)    
        
    # Construct command to execute simulations
    programStr = os.path.join(obj_simRunner.sourceFiles, 'Animatsimulator')        
    listArgs = [programStr]
    
    return listArgs
    
    # Copy simulation file to common project folder
    pathOrigSim = os.path.join(obj_simRunner.simFiles, asimFile)
    pathTempSim = os.path.join(fldrActiveFiles, asimFile)
    shutil.copy2(pathOrigSim, pathTempSim)
    
    # Create simulation shell command
    strArg = os.path.join(fldrActiveFiles, asimFile)
    listArgs.append(strArg)
    
    # Send shell command
    #subprocess.call(listArgs)
                
    # Delete temporary simulation file from common project folder
    os.remove(pathTempSim)            
    
    # Copy data files to resultsFolder
    obj_simRunner._each_callback_fn(sourceFolder=fldrActiveFiles, name=asimFile.split('.')[0])                
    
    # Delete temporary model folder
    shutil.rmtree(fldrActiveFiles)   
    
        
        
class AnimatLabSimulationRunner(object):
    """
    animatLabSimulationRunner(simRunnerName, rootFolder, commonFiles, sourceFiles, simFiles, resultFiles='')
    API class to iterate through AnimatLab simulation files (*.asim) organized in a folder.
    This tool is analogous to the SimRunner utility included in the AnimatLab SDK.
    
    simRunnerName     Unique name for sim runner object instance
    rootFolder        Full path of folder within which all other folders are saved
    commonFiles       Full path of AnimatLab project folder (contains *.aproj file)
    sourceFiles       Full path to AnimatLab binary exectuable (contains AnimatLab.exe)
    simFiles          Full path to AnimatLab simualtion files (contains *.asim files)
    resultFiles       Full path to folder where result files will be saved
    
    do_simulation()          Run simulation set in simFiles folder using the defined parameters
    set_each_callback(fn)    Set a callback function to execute upon completing EACH simulation
    _each_callback_fn()      Executes callback after EACH simulation is complete
    set_master_callback(fn)  Set a callback function to execute upon completing ALL simulations
    _master_callback_fn()    Dummy method to be defined by user
    """
    
    def __init__(self, simRunnerName, rootFolder, commonFiles, sourceFiles, simFiles, resultFiles=''):
        """
        __init__(simRunnerName, rootFolder, commonFiles, sourceFiles, simFiles, resultFiles='')
        
        simRunnerName     Unique name for sim runner object instance
        rootFolder        Full path of folder within which all other folders are saved
        commonFiles       Full path of AnimatLab project folder (contains *.aproj file)
        sourceFiles       Full path to AnimatLab binary exectuable (contains AnimatLab.exe)
        simFiles          Full path to AnimatLab simualtion files (contains *.asim files)
        resultFiles       Full path to folder where result files will be saved
        
        If resultFiles is left empty, simulation result data will be saved to the root folder.
        
        Last updated:   January 4, 2016
        Modified by:    Bryce Chung
        """
        
        self.name = simRunnerName
        self.rootFolder = rootFolder
        self.commonFiles = commonFiles
        self.sourceFiles = sourceFiles

        self.simFiles = simFiles
        self.resultFiles = resultFiles
        
        
    def do_simulation(self, cores=None):
        """
        do_simulation()
        
        1. Check for validity of simulation folders to use while running simulations.
        2. Run simulations and post process data as simulations are completed
        3. Remove temporary files and folders
        
        Last updated:   January 4, 2016
        Modified by:    Bryce Chung
        """
        
        # Check that root folder exists
        if not os.path.isdir(self.rootFolder):
            raise AnimatLabSimRunnerError("Root folder does not exist!\n%s" % self.rootFolder)
        
        # Check that common model files exist
        if not os.path.isdir(self.commonFiles):
            raise AnimatLabSimRunnerError("Common files folder does not exist!\n%s" % self.commonFiles)
        else:
            if len(glob.glob(os.path.join(self.commonFiles, '*.aproj'))) < 1:
                raise AnimatLabSimRunnerError("No AnimatLab project files found in common files folder.\n%s" % self.commonFiles)
        
        # Check that source files with AnimatLab binaries exist
        if not os.path.isdir(self.sourceFiles):
            raise AnimatLabSimRunnerError("Source files folder does not exist!\n%s" % self.sourceFiles)
        else:
            if len(glob.glob(os.path.join(self.sourceFiles, 'Animatsimulator.exe'))) < 1:
                raise AnimatLabSimRunnerError("AnimatLab Sim Runner program not found in source files folder.\n%s" % self.sourceFiles)
        
        # Check that simulation files exist in folder
        if not os.path.isdir(self.simFiles):
            raise AnimatLabSimRunnerError("Simulation folder does not exists.\n%s" % self.simFiles)
        else:
            if len(glob.glob(os.path.join(self.simFiles, '*.asim'))) < 1:
                raise AnimatLabSimRunnerError("No simulation files found in simulation folder.\n%s" % self.simFiles)        
        
        # Check that results folder exists
        if self.resultFiles == '':
            self.resultFiles = self.rootFolder
        else:
            if not os.path.isdir(self.resultFiles):
                os.makedirs(self.resultFiles)        
        
        # Construct command to execute simulations
        programStr = os.path.join(self.sourceFiles, 'Animatsimulator')
        
        if verbose > 1:
            print "\n\n========================="
            print "\nSIMULATION SERIES: %s" % self.name
            print "\n========================="
        
        # Iterate through *.asim files and execute simulations
        if cores is None:
            # Make a copy of common model files to use during simulations
            fldrActiveFiles = os.path.join(self.rootFolder, self.name)
            if os.path.isdir(fldrActiveFiles):
                dirs = [d for d in os.listdir(self.rootFolder) if self.name in d]
                count = 0
                for d in dirs:
                    if os.path.isdir(os.path.join(self.rootFolder, d)):
                        count += 1
                fldrActiveFiles = os.path.join(self.rootFolder, self.name+'-'+str(count))
            shutil.copytree(self.commonFiles, fldrActiveFiles)            
            
            for simFile in os.listdir(self.simFiles):
                if verbose > 1:
                    print "\n\nPROCESSING SIMULATION FILE: %s" % simFile
                    
                listArgs = [programStr]
                
                # Copy simulation file to common project folder
                pathOrigSim = os.path.join(self.simFiles, simFile)
                pathTempSim = os.path.join(fldrActiveFiles, simFile)
                shutil.copy2(pathOrigSim, pathTempSim)
                
                # Create simulation shell command
                strArg = os.path.join(fldrActiveFiles, simFile)
                listArgs.append(strArg)
                
                ## For debugging
                #print listArgs
                #raw_input("Press <ENTER> to continue.")
                
                # Send shell command
                #subprocess.call(listArgs)
                            
                # Delete temporary simulation file from common project folder
                os.remove(pathTempSim)            
                
                # Copy data files to resultsFolder
                self._each_callback_fn(sourceFolder=fldrActiveFiles, name=simFile.split('.')[0])                
                
                # Delete temporary model folder
                shutil.rmtree(fldrActiveFiles)                
        else:
            
            if cores > 0:
                pool = multiprocessing.Pool(processes=cores)
            else:
                pool = multiprocessing.Pool()
                
            self.results = pool.map(runAnimatLabSimulationWrapper, [(ix, filename, copy(self)) for ix, filename in enumerate(os.listdir(self.simFiles)[0:15])]) 
                



    def set_each_callback(self, fn):
        """
        set_each_callback(fn)
        
        fn    User-defined callback function to execute after EACH simulation
        
        Last updated:   January 4, 2016
        Modified by:    Bryce Chung
        """
        
        pass


    def _each_callback_fn(self, sourceFolder='', name=''):
        """
        _each_callback_fun()
        
        Default callback function that copies the results files for each simulation
        to the resultsFolder.
        
        Last updated:   January 4, 2016
        Modified by:    Bryce Chung
        """
        
        # Save chart result files to results folder
        for f in glob.glob(os.path.join(sourceFolder, '*.txt')):
            fname = str(name) + "_" + os.path.split(f)[-1].split('.')[0]
            ix = len(glob.glob(os.path.join( self.resultFiles, fname.split('.')[0]+'*.asim' )))
            if ix > 0:
                fname += '-%i' % ix
            shutil.copy2(f, os.path.join(self.resultFiles, fname))
            # Remove results file from commonFiles folder
            os.remove(f)


    def set_master_callback(self, fn):
        """
        set_master_callback(fn)
        
        fn    User-defined callback function to execute after ALL simulations are complete
        
        Last updated:   January 4, 2016
        Modified by:    Bryce Chung
        """
        
        pass
