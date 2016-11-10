from typing import List, Union
from Util import find_value
import Telescope
import subprocess
import Util
import time
import os


class Session(object):
    """
    This class represents a single imaging session that will image each target with 
    the chosen number of exposures where each exposure is exposure_time seconds long.
    By default, science frames with each of the three primary filters will be taken, 
    as well as clear darks, biases and flats. 
    """
    
    def __init__(self, targets: List[str],
                 exposure_time: float,
                 exposure_count: int = 1,
                 filters: List[str] = ["clear"],
                 binning: int = 2,
                 user: str = "",
                 nodark: bool = False, 
                 nobias: bool = False):
        """ Creates a new imaging session with desired parameters.

        Creates a new imaging session that will image each target with exposure_count 
        exposures where each exposure is exposure_time seconds long. 

        Args:
            targets: a list of strings identifying targets to be imaged, i.e.
                    ['m31, 'C 34', 'NGC 6974']
            exposure_time: the time for each exposure in seconds
            exposure_count: the number of exposures to take for each filter
            filters: a list of strings indicating the desired filters for each exposure
            binning: the desired CCD binning
            user: the username of the user who requested/created the session
        """

        # get user
        self.user = user
        
        self.__log("Creating new imaging session for user: "+str(self.user)+"...",
                   color="green")
        
        # A list of strings containing catalog names of objects to be imaged
        # Currently, the objects are imaged in the order they are specified.
        self.targets = targets
        self.__log("Session Targets: "+str(self.targets))

        # The exposure time in seconds for each science image
        self.exposure_time = exposure_time
        self.__log("Exposure Time: "+str(self.exposure_time)+"s")

        # The number of science images to be taken per filter/clear
        self.exposure_count = exposure_count
        self.__log("Exposure Count: "+str(self.exposure_count))

        # Whether I, R, G filters should be used 
        self.filters = filters
        self.__log("Using filters: "+str(self.filters))

        # What binning to use
        self.binning = binning
        self.__log("CCD Binning: "+str(self.binning))

        # assign the telescope
        self.telescope = Telescope.Telescope(nodark=nodark, nobias=nobias)

        
    def execute(self) -> int: 
        """ Starts the execution of the imaging session; return's status
        once imaging run is completed. 
        """

        # check if the dome is already open
        if self.telescope.dome_status() is False: # dome is closed
            self.telescope.open_dome()
            
        # image each target
        for target in self.targets:

            # enable tracking again as a precaution
            self.telescope.enable_tracking()

            # check whether object is visible, and try slewing the
            # telescope to point at object
            if self.telescope.goto_target(target) is False:
                self.__log("Unable to point telescope at "+target+". Object"
                           " is most likely not visible or there has been a"
                           " telescope error. Skipping "+target+"...", color="red")
                continue # try imaging next target

            # variables to produce seo file format name
            year = time.strftime("%Y", time.gmtime()) # 2016
            month = time.strftime("%B", time.gmtime())[0:3].lower() # oct
            day = time.strftime("%d", time.gmtime()) # 07
            base_name = "-band_"+str(self.exposure_time)+"sec"
            base_name += "_bin"+str(self.binning)+"_"+year+month+day+"_"
            base_name += self.user+"_num"

            # how many darks we have taken
            dark_count = 0
            
            # take exposures for each filter
            for f in filters:

                #enable tracking as a precaution
                self.telescope.enable_tracking()
                
                self.telescope.change_filter(f)
                # take exposures! 
                for n in range(self.exposure_count):
                    filename = str(target)+"_"+str(f)+base_name+str(n)+"_seo"
                    self.__log("Taking exposure {} for {}".format(n, target))
                    self.telescope.take_exposure(filename)

                filename = str(target)+"_dark"+base_name+str(dark_count)+"_seo"
                dark_count += 1
                self.telescope.take_dark(filename)

            # reset filter to clear
            self.telescope.change_filter('clear')

            # take any leftover darks
            for n in range(dark_count, self.exposure_count):
                filename = str(target)+"_dark"+base_name+str(n)+"_seo"
                self.telescope.take_dark(filename)

            # take exposure count biases
            for n in range(10*self.exposure_count):
                filename = str(target)+"_bias"+base_name+str(n)+"_seo"
                self.telescope.take_bias(filename)

            self.close()

        return True


    def __log(self, msg: str, color: str = "white") -> bool:
        """ Prints a log message to STDOUT. Returns True if successful, False
        otherwise.
        """
        return Util.log(msg, color)    
