# This file implements a Server that listens for requests from Submit programs
# to add Sessions to the queue for tonight's imaging session
import zmq
import time
import typing
import signal
import sys
import json

class Server(object):
    """ This class represents a server that listens for queueing requests from 
    clients; once it has received a request, process_message() is called, which
    adds the request to the queue.
    """

    def __init__(self, port: int = 27748, queuename: str = ""):
        """ This creates a new server listening on the specified port; this does
        not start the server listening, it just creates the server. start() must
        be called for the server to be initialized. 

        port: the port to listen on
        queuename: string to be prepended to the imaging queuelog
        """
        self.__log("Creating new queue server...", color="green")
        # the port to be used for communication
        self.port = str(port)

        # magic number for imaging requests
        self.magic = 392919

        # magic number for admin requests
        self.magic_admin = 1224580

        # whether we are enabled
        self.enabled = False

        # zeroMQ context
        self.context = zmq.Context()

        # zeroMQ socket
        self.socket = self.context.socket(zmq.REP)

        # connect socket
        self.socket.bind("tcp://*:%s" % self.port)
        self.__log("Bound server to socket %s" % self.port)

        # file name for JSON store
        currdate = time.strftime("%Y-%m-%d", time.gmtime())
        self.filename = queuename+currdate+"_imaging_queue.json"
        self.file = open(self.filename, 'w')
        if self.file is None:
            self.__log("Unable to open queue!", color="red")
        self.__log("Storing queue in %s" % self.filename)
        self.file.close()

        # create a handler for SIGINT
        signal.signal(signal.SIGINT, self.handle_exit)
        

    def handle_exit(self, signal, frame):
        """ SIGINT handler to check for Ctrl+C for quitting the server. 
        """
        print("\033[1;31mAre you sure you would like to quit [y/n]?\033[0m")
        choice = input().lower()
        if choice == "y" or choice == "Y":
            print("\033[1;31mQuitting server...\033[0m")
            self.file.close()
            sys.exit(0)
        
    def __del__(self):
        """ Called when the server is garbage collected - at this point, 
        this function does nothing.
        """
        pass

        
    def start(self):
        """ Starts the servers listening for new requests; server blocks
        on the specified port until it receives a request
        """
        while True:
            message = json.loads(self.socket.recv_json())
            if message["magic"] == self.magic:
                self.__log("Received imaging request from {}...".format(message["user"]))
                self.save_request(message)
                self.socket.send_string(str(self.magic))
            elif message["magic"] == self.magic_admin:
                self.__log("Received message from {}...".format(message["user"]))
                self.process_message(message)
                self.socket.send_string(str(self.magic_admin))
            else:
                self.__log("Received invalid message from a client...")
            
    def __log(self, msg: str, color: str = "white") -> bool:
        """ Prints a log message to STDOUT. Returns True if successful, False
        otherwise.
        """
        colors = {"red":"31", "green":"32", "blue":"34", "cyan":"36",
                  "white":"37", "yellow":"33", "magenta":"34"}
        logtime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        log = "\033[1;"+colors[color]+"m"+logtime+" SERVER: "+msg+"\033[0m"
        print(log)
        return True

    
    def enable(self) -> bool:
        """ Enable the queue server to start taking imaging requests
        """
        self.enabled = True

        
    def disable(self) -> bool:
        """ Disable the queue server from taking any requests. 
        """
        self.enabled = False


    def save_request(self, msg: str) -> list:
        """ This takes a raw message from zmq and writes the JSON data
        into the queue file. 
        """
        self.file = open(self.filename, "a")
        self.file.write(json.dumps(msg)+"\n")
        self.file.close()

    def process_message(self, msg: str) -> list:
        """ This processes an admin message to alter the server state.
        """
        if msg['type'] == 'state':
            if msg['action'] == 'enable':
                self.__log("Enabling queueing server...", color="cyan")
                self.enabled = True
            elif msg['action'] == 'disable':
                self.__log("Disabling queueing server...", color="cyan")
                self.enabled = False
            else:
                self.__log("Received invalid admin state message...", color="magenta")
        else:
            self.__log("Received unknown admin message...", color+"magenta")
