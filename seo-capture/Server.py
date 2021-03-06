# This file implements a Server that listens for requests from Submit programs
# to add Sessions to the queue for tonight's imaging session
import zmq
import time
import typing
import signal
import sys
import json
import yaml
import os
import requests

class Server(object):
    """ This class represents a server that listens for queueing requests from 
    clients; once it has received a request, process_message() is called, which
    adds the request to the queue.
    """

    def __init__(self, port: int = 0, queuename: str = ""):
        """ This creates a new server listening on the specified port; this does
        not start the server listening, it just creates the server. start() must
        be called for the server to be initialized. 

        port: the port to listen on
        queuename: string to be prepended to the imaging queuelog
        """

        if os.path.isfile("config.yaml"):
            stream = open("config.yaml", 'r')
            config = yaml.load(stream)
        else:
            exit("\033[1;31mServer unable to find config.yaml. Exiting...\033[0m")
            
        self.__log("Creating new queue server...", color="green")
        # the port to be used for communication
        if port == 0:
            self.port = config["server"]["port"]
        else:
            self.port = port

        # magic number for imaging requests
        self.magic = config["server"]["request_magic"]

        # magic number for admin requests
        self.magic_admin = config["server"]["admin_magic"]

        # whether we are enabled
        if config["server"]["default"] == "on":
            self.enabled = True
        else:
            self.enabled = False

        # zeroMQ context
        self.context = zmq.Context()

        # zeroMQ socket
        self.socket = self.context.socket(zmq.REP)

        # connect socket
        self.socket.bind("tcp://*:%s" % self.port)
        self.__log("Bound server to socket %s" % self.port)

        # file name for JSON store
        qdir = config["server"]["queue_dir"]
        currdate = time.strftime("%Y-%m-%d", time.gmtime())
        self.filename = qdir+"/"+queuename+currdate+"_imaging_queue.json"
        self.file = open(self.filename, 'w')
        if self.file is None:
            self.__log("Unable to open queue!", color="red")
        self.__log("Storing queue in %s" % self.filename)
        self.file.close()

        #twilight for the day and time functions
        time.timezone = 8*3600 #Sonoma, Cali is UTC-8
        self.twilight = self.getTwilightToday()
        self.closedqueue = False

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



    #gets twilight for the given day
    def getTwilightToday(day):
        urllist = []
        urllist.append("aa.usno.navy.mil/rstt/onedaytable?ID=AA?year=")
        urllist.append(str(day[0]))
        urllist.append("&month=")
        urllist.append(str(day[1]))
        urllist.append("&day=")
        urllist.append(str(day[2]))
        urllist.append("&state=CA&place=Sonoma")
        url = ''.join(urllist)
        r = requests.get(url)
        hour = int(r.text[2581:2582])+12
        minute = int(r.text[2583:2585])    #<--- this fails currently as there is slight variance in length of page
        #EG http://aa.usno.navy.mil/rstt/onedaytable?ID=AA&year=2016&month=12&day=15&state=CA&place=Sonoma
        

        return time.struct_time(day[0],day[1],day[2],18,0,0,day[6],day[7],day[8])
        

    #checks if it is currently later than twilight
    def laterThanTwilight(self):
        lt = time.localtime
        tw = self.twilight
        #this is ugly, should write a comparison function for struct_time objects
        if(lt[3]>tw[3] or (lt[3]==tw[3] and (lt[4]>tw[4] or (lt[4]==tw[4] and lt[5]>tw[5])))):
            return True
        return False


    

    #given a struct_time object, increments it by one day
    #this function is super gross...
    def incrementDay(day):
        if(day[1]==1):
            if(day[2]==31):
                return time.struct_time(day[0],2,1,day[3],day[4],day[5],day[6],day[7],day[8])
            return time.struct_time(day[0],1,day[2]+1,day[3],day[4],day[5],day[6],day[7],day[8])
        elif(day[1]==2):
            if(day[2]==29):
                return time.struct_time(day[0],3,1,day[3],day[4],day[5],day[6],day[7],day[8])
            elif(day[2]==28):
                if(day[0]%4==0):
                    return time.struct_time(day[0],2,29,day[3],day[4],day[5],day[6],day[7],day[8])
                return time.struct_time(day[0],3,1,day[3],day[4],day[5],day[6],day[7],day[8])
            return time.struct_time(day[0],2,day[2]+1,day[3],day[4],day[5],day[6],day[7],day[8])
        elif(day[1]==3):
            if(day[2]==31):
                return time.struct_time(day[0],4,1,day[3],day[4],day[5],day[6],day[7],day[8])
            return time.struct_time(day[0],3,day[2]+1,day[3],day[4],day[5],day[6],day[7],day[8])
        elif(day[1]==4):
            if(day[2]==30):
                return time.struct_time(day[0],5,1,day[3],day[4],day[5],day[6],day[7],day[8])
            return time.struct_time(day[0],4,day[2]+1,day[3],day[4],day[5],day[6],day[7],day[8])
        elif(day[1]==5):
            if(day[2]==31):
                return time.struct_time(day[0],6,1,day[3],day[4],day[5],day[6],day[7],day[8])
            return time.struct_time(day[0],5,day[2]+1,day[3],day[4],day[5],day[6],day[7],day[8])
        elif(day[1]==6):
            if(day[2]==30):
                return time.struct_time(day[0],7,1,day[3],day[4],day[5],day[6],day[7],day[8])
            return time.struct_time(day[0],6,day[2]+1,day[3],day[4],day[5],day[6],day[7],day[8])
        elif(day[1]==7):
            if(day[2]==31):
                return time.struct_time(day[0],8,1,day[3],day[4],day[5],day[6],day[7],day[8])
            return time.struct_time(day[0],7,day[2]+1,day[3],day[4],day[5],day[6],day[7],day[8])
        elif(day[1]==8):
            if(day[2]==31):
                return time.struct_time(day[0],9,1,day[3],day[4],day[5],day[6],day[7],day[8])
            return time.struct_time(day[0],8,day[2]+1,day[3],day[4],day[5],day[6],day[7],day[8])
        elif(day[1]==9):
            if(day[2]==30):
                return time.struct_time(day[0],10,1,day[3],day[4],day[5],day[6],day[7],day[8])
            return time.struct_time(day[0],9,day[2]+1,day[3],day[4],day[5],day[6],day[7],day[8])
        elif(day[1]==10):
            if(day[2]==31):
                return time.struct_time(day[0],11,1,day[3],day[4],day[5],day[6],day[7],day[8])
            return time.struct_time(day[0],10,day[2]+1,day[3],day[4],day[5],day[6],day[7],day[8])
        elif(day[1]==11):
            if(day[2]==30):
                return time.struct_time(day[0],12,1,day[3],day[4],day[5],day[6],day[7],day[8])
            return time.struct_time(day[0],11,day[2]+1,day[3],day[4],day[5],day[6],day[7],day[8])
        else: #assuming this means it is december
            if(day[2]==31):
                return time.struct_time(day[0]+1,1,day[3],day[4],day[5],day[6],day[7],day[8])
            return time.struct_time(day[0],12,day[2]+1,day[3],day[4],day[5],day[6],day[7],day[8])
        ###END FUNCTION incrementDay()###############

                

    #creates the queue file for the next day
    def queueNextDay(self):
        qdir = config["server"]["queue_dir"]
        currdate = time.strftime("%Y-%m-%d", incrementDay(time.gmtime()))
        self.filename = qdir+"/"+queuename+currdate+"_imaging_queue.json"
        self.file = open(self.filename, 'w')
        if self.file is None:
            self.__log("Unable to open queue!", color="red")
        self.__log("Storing queue in %s" % self.filename)
        self.file.close()



        
    def start(self):
        """ Starts the servers listening for new requests; server blocks
        on the specified port until it receives a request
        """
        while True:
            laterthantwilight = self.laterThanTwilight()
            if(laterthantwilight and not self.closedqueue):
                self.queueNextDay()
                self.closedqueue = True
            elif(self.closedqueue and not laterthantwilight):
                #it is now the next day
                self.twilight = self.getTwilightToday()
                self.closedqueue = False

            
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
