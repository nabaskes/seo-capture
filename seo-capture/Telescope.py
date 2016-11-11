# This file provides an abstraction around the control commands for the telescope; no shell commands
# should be run except through the Telescope interface provided below

import typing
import subprocess
import Util

class Telescope(object):

    def __init__(self, nodark: bool = False, nobias: bool = False):
        # something here?
        self.nodark = nodark
        self.nobias = nobias

    def open_dome(self) -> bool:
        """ Checks that the weather is acceptable, and then opens the dome, 
        if it is not already open, and  also enables tracking. 
        """
        # check if dome is already open
        if self.__dome_status() == True:
            return True

        # check that weather is OK to open
        if self.__weather_ok() == True:
            result = self.__run_command("openup nocloud &&" 
                                        "keepopen maxtime=20000 slit"
                                        "&& track on")
            if result == True: # everything was good
                return True
            else: # one of the commands failed
                return False
        else:
            return False

    
    def close_dome(self) -> bool:
        """ Closes the current session, closes the dome, and logs out. Returns
        True if successful in closing down, False otherwise.
        """
        return self.__run_command("closedown && logout")

    
    def weather_ok(self) -> bool:
        """ Checks whether the sun has set, there is no rain (rain=0) and that 
        it is less than 40% cloudy. Returns true if the weather is OK to open up, 
        false otherwise. 
        """

        # check sun
        sun = self.__run_command("sun")
        if float(find_value("alt", sun)) >= -1.0:
            return False

        # sun is good - check for weather
        weather = self.__run_command("tx taux")

        # if this cmd failed, return false to be safe
        if weather == None or weather == "":
            return False
        
        rain = 1 # default to being raining just in case
        cloud = 1 # default to being cloudy just in case
        rain = float(find_value("rain", weather)) # find rain=val
        cloud = float(find_value("cloud", weather)) # find cloud=val

        if rain == 0 and cloud < 0.4:
            return True
        else:
            return False

    
    def dome_status(self) -> str:
        """ Checks whether the slit is open or closed. Returns True if open, 
        False if closed.
        """
        slit = self.__run_command("tx slit")
        result = find_value("slit", slit)
        if result == "open":
            return True

        return False

    
    def goto_target(self, name: str) -> bool:
        # JUST AN IDEA
        """ Points the telescope at the target in question. Returns True if
        successfully (object was visible), and returns False if unable to set
        telescope (failure, object not visible).
        """
        if self.__target_visible(target) == True:
            cmd = "catalog "+target+" | dopoint"
            return self.__run__command(cmd)

        return False

    
    def target_visible(self, name: str) -> bool:
        # JUST AN IDEA
        """ Checks whether a target is visible, and whether it is > 40 degrees
        in altitude. Returns True if visible and >40, False otherwise
        """
        cmd = "catalog "+target+" | altaz"
        altaz = self.__run_command(cmd).split()
        if float(find_value("alt", altaz)) >= 40:
            return True

        return False

    
    def current_filter(self) -> str:
        """ Returns the name of the currently enabled filter, or
        clear otherwise. 
        """
        return self.__run_command("pfilter")

    
    def change_filter(self, name: str) -> str:
        # JUST AN IDEA
        """ Changes filter to the new specified filter. Options are: 
        u, g, r, i, z, clear, h-alpha. Returns True if successful, 
        False otherwise
        """
        if name == "h-alpha":
            return self.__run_command("pfilter h-alpha")
        elif name == "clear":
            return self.__run_command("pfilter clear")
        else:
            return self.__run_command("pfilter "+name+"-band")

    
    def take_exposure(self, filename: str) -> bool:
        # Juat an idea
        """ Takes an exposure of length self.exposure_time saves it in the FITS 
        file with the specified filename. Returns True if imaging
        was successful, False otherwise. 
        """
        cmd = "image time="+self.exposure_time+" bin="+self.binning+" "
        cmd += "outfile="+filename+".fits"
        status = self.__run_command(cmd)
        self.__log("Saved exposure frame to "+filename, color="cyan")
        return status

    
    def take_bias(self, filename: str) -> bool:
        # JUST AN IDEA
        """ Takes a bias frame and saves it in the FITS file with the specified
        filename. Returns True if imaging was successful, False otherwise. 
        """
        if not self.nobias:
            cmd = "image time=0.5 bin="+self.binning+" "
            cmd += "outfile="+filename+"_bias.fits"
            status = self.__run_command(cmd)
            self.__log("Saved bias frame to "+filename, color="cyan")
            return status
        return True

    
    def take_dark(self, filename: str) -> bool:
        ## AMANDA, THIS IS JUST AN IDEA - WORTH A REWRITE
        """ Takes an dark exposure of length self.exposure_time saves it in the
        FITS file with the specified filename. Returns True if imaging
        was successful, False otherwise. 
        """
        if not self.nodark:
            cmd = "image time="+self.exposure_time+" bin="+self.binning+" dark "
            cmd += "outfile="+filename+"_dark.fits"
            status = self.__run_command(cmd)
            self.__log("Saved dark frame to "+filename, color="cyan")
            return status
        return True

    
    def enable_tracking(self) -> bool:
        pass

    
    def focus(self) -> bool:
        pass

    
    def enable_flats(self) -> bool:
        # run tin?
        pass

    
    def offset(self) -> bool:
        pass
    

    def __log(self, msg: str, color: str = "white") -> bool:
        """ Prints a log message to STDOUT. Returns True if successful, False
        otherwise.
        """
        return Util.log(msg, color)    

    
    def __run_command(self, command: str) -> str:
        """ Executes a shell command either locally, or remotely via ssh. 
        Returns the byte string representing the captured STDOUT
        """
        self.__log("Executing {}".format(command), color="magenta")
        try:
            return subprocess.check_output(command)
        except:
            self.__log("Failed while executing {}".format(command), color="red")
            self.__log("Please manually close the dome by running"
                       " `closedown` and `logout`.", color="red")
            exit(1)
