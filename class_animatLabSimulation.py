"""
Created by:      Bryce Chung
Last modified:   January 4, 2016

Description:     This class allows the user to run AnimatLab simulations from Python.
"""

# Import dependencies
import os, glob, shutil
import subprocess

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
        
class animatLabSimulationRunner(object):
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
        """
        
        self.name = simRunnerName
        self.rootFolder = rootFolder
        self.commonFiles = commonFiles
        self.sourceFiles = sourceFiles

        self.simFiles = simFiles
        self.resultFiles = resultFiles
        
        # Initialize callback function for each simulation
        self.each_callback = self._each_callback_fn
        
        
    def do_simulation(self):
        """
        1. Check for validity of simulation folders to use while running simulations.
        2. Run simulations and post process data as simulations are completed
        3. Remove temporary files and folders
        """
        ## Check that root folder exists
        if not os.path.isdir(self.rootFolder):
            raise AnimatLabSimRunnerError("Root folder does not exist!\n%s" % self.rootFolder)
        
        ## Check that common model files exist
        if not os.path.isdir(self.commonFiles):
            raise AnimatLabSimRunnerError("Common files folder does not exist!\n%s" % self.commonFiles)
        else:
            if len(glob.glob(os.path.join(self.commonFiles, '*.aproj'))) < 1:
                raise AnimatLabSimRunnerError("No AnimatLab project files found in common files folder.\n%s" % self.commonFiles)
        
        ## Make a copy of common model files to use during simulations
        shutil.copytree(self.commonFiles, os.path.join(self.rootFolder, self.name))
        
        ## Check that source files with AnimatLab binaries exist
        if not os.path.isdir(self.sourceFiles):
            raise AnimatLabSimRunnerError("Source files folder does not exist!\n%s" % self.sourceFiles)
        else:
            if len(glob.glob(os.path.join(self.sourceFiles, 'Animatsimulator.exe'))) < 1:
                raise AnimatLabSimRunnerError("AnimatLab Sim Runner program not found in source files folder.\n%s" % self.sourceFiles)
        
        ## Check that simulation files exist in folder
        if not os.path.isdir(self.simFiles):
            raise AnimatLabSimRunnerError("Simulation folder does not exists.\n%s" % self.simFiles)
        else:
            if len(glob.glob(os.path.join(self.simFiles, '*.asim'))) < 1:
                raise AnimatLabSimRunnerError("No simulation files found in simulation folder.\n%s" % self.simFiles)        
        
        ## Check that results folder exists
        if self.resultFiles == '':
            self.resultFiles = self.rootFolder
        else:
            if not os.path.isdir(self.resultFiles):
                os.makedirs(self.resultFiles)        
        
        programStr = os.path.join(self.sourceFiles, 'Animatsimulator')
        
        if verbose > 1:
            print "\n\n========================="
            print "\nSIMULATION SERIES: %s" % self.name
            print "\n========================="
        
        for simFile in os.listdir(self.simFiles):
            if verbose > 1:
                print "\n\nPROCESSING SIMULATION FILE: %s" % simFile
                
            listArgs = [programStr]
            
            ## Copy simulation file to common project folder
            pathOrigSim = os.path.join(self.simFiles, simFile)
            pathTempSim = os.path.join(self.commonFiles, simFile)
            shutil.copy2(pathOrigSim, pathTempSim)
            
            ## Create simulation shell command
            strArg = os.path.join(self.commonFiles, simFile)
            listArgs.append(strArg)
            
            ## Send shell command
            #print listArgs
            #raw_input("Press <ENTER> to continue.")
            subprocess.call(listArgs)
                        
            ## Delete temporary simulation file from common project folder
            os.remove(pathTempSim)            
            
            ## Copy data files to resultsFolder
            self._each_callback_fn()
            
            ## Call post-process function
            self.each_callback()

            
        ## Delete temporary model folder
        shutil.rmtree(os.path.join(self.rootFolder, self.name))
        
        ## Execute master callback function
        self.master_callback()

    def set_each_callback(self, fn):
        self.each_callback = fn

    def _each_callback_fn(self):
        ## Save chart result files to results folder
        for f in glob.glob(os.path.join(self.commonFiles, '*.txt')):
            shutil.copy2(f, os.path.join(self.resultFiles, f))
            os.remove(f)

    def set_master_callback(self, fn):
        self.master_callback = fn
        
