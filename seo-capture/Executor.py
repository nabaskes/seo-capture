import json
import time
import typing
import Util
import Session

class Executor(object):
    """ This class is responsible for executing and scheduling a 
    list of Sessions stored in the JSON queue constructed by the Server. 
    """

    def __init__(self, filename: str):
        """ This creates a new executor to execute a single nights
        list of Sessions stored in the JSON file specified by filename. 
        """

        # filename to be read
        self.filename = filename

        # load queue from disk
        self.sessions = []
        self.load_queue(self.filename)

        # create a handler for SIGINT
        signal.signal(signal.SIGINT, self.handle_exit)

        
    def load_queue(self, filename: str) -> list:
        """ This loads a JSON queue file into a list of Python session
        objects that can then be executed. 
        """

        def json_to_session(msg) -> Session:
            """ Converts the dictionary representation of a queue request
            into a Session object. """
            s = Session.Session(targets = msg['targets'],
                        exposure_time = msg['exposure_time'], 
                        exposure_count = msg['exposure_count'], 
                        filters = msg['filters'], 
                        binning = msg['binning'],
                        user = msg['user'])
            return s
                    
        with open(self.filename) as queue:
            for line in queue:
                self.sessions.append(json_to_session(json.loads(line)))

    def execute_queue(self) -> bool:
        """ Executes the list of session objects for this queue. 
        """
        count = 1
        for session in self.sessions:
            # check whether every session executed correctly
            self.__log("Executing session: {}".format(count), color="cyan")
            if not session.execute():
                return False
            count += 1

        return True



    def __log(self, msg: str, color: str = "white") -> bool:
        """ Prints a log message to STDOUT. Returns True if successful, False
        otherwise.
        """
        return Util.log(msg, color)


    def handle_exit(self, signal, frame):
        """ SIGINT handler to check for Ctrl+C for quitting the executor. 
        """
        print("\033[1;31mAre you sure you would like to quit [y/n]?\033[0m")
        choice = input().lower()
        if choice == "y" or choice == "Y":
            print("\033[1;31mQuitting executor and closing the dome...\033[0m")
            if len(self.sessions) > 0:
                self.session[0].telescope.close_dome()
            sys.exit(0)
