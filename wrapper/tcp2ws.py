#! /usr/bin/python
import socket, select
import threading
import time
import bridgeObject, tcpserver, wsclient
import sys
import os
from websocket import create_connection
import signal


#TODO: - proper exception handling!
#        -> don't catch "universal" Exception everywhere!!!!
#TODO: - keep a socket open to rosbridge to check its availability
#        or just check every ~10s, ...
#TODO: - check for first and last bytes of message.. maybe they need to be cut off
#        -> looks like it's working without these bytes (for rosbridge v2)
#TODO: - do proper commandline parameter parsing (and value checking!)
#TODO: - implement interrupting tcp2ws by pressing ctrl-c on shell.
#        * catch KeyboardInterrupt in main loop;
#        * in ALL other try-catch change from (universal) Exception to specific exceptions..
#        * (problem now, is that KeyboardInterrupt gets catched by "some "any" catch-clause...
#        *   -> first workaround was to add "except keyboard.. .. sys.exit" to any try-catch
#        -> not solved yet, running tcp2ws using upstart/start-stop-daemon might work
#        * maybe add one more thread for a loop to check for keyboardInterruptions..
#          -> 1 for keyboard,
#             1 for listening socket,
#             2 for each bridgeObject (tcp-socket & websocket)
#TODO: - add proper logging
#        * INFO, WARN, ERROR, .. levels
#        * logging to a file;
#        * remove unnecessary logs; keep or add log for relevant information
#TODO: - describe concept, components, dependencies...
#TODO: - add client info to console output: IP, port, ...

#TODO: finish all todo's in tcpserver, wsclient, bridgeObject



# ########################## description #######################################
# ...nothing here yet
# ########################## end of description ################################



# basic instructions, shown at programm start
basic_instructions =  "possible parameters:\n"
basic_instructions += "--listening_address <value>              listening tcp address (default: 0.0.0.0)\n"
basic_instructions += "--listening_port <value>                 listening tcp port (default: 9095)\n"
basic_instructions += "--rosbridge_address <value>              ros-bridge address (default: localhost)\n"
basic_instructions += "--rosbridge_port <value>                 ros-bridge port (default: 9090)\n"
basic_instructions += "--max_msg_len <value>                    maximum message length in bytes (default: 1024)\n"
basic_instructions += "\n"


# config stuff
listening_address = ""                                                          # "" accepts connections on all active addresses
listening_port = 9095
rosbridge_ip = "localhost"                                                      # IP or hostname
rosbridge_port = 9090
max_message_length = 1024
listening_delay_s = 0.01                                                        # maybe add socket timeouts.. <-- testing/reviewing/...
listening_timeout = 1
working_dir = "."


# logging stuff
logfile = "tcp2ws.log"
print "path:", os.system("pwd")
#print "user:", os.system("who am i")



# main class
class TCP2WS (threading.Thread):                                                
    bridge_list = []                                                            # list of existing bridges, one for each existing connection
    listening_socket = None                                                     # socket listening for incoming tcp connections
    default_parameter = {}                                                      # set default parameters:
    default_parameter["listening_address"] = listening_address                  # "" accepts connections on all active addresses
    default_parameter["listening_port"] = listening_port
    default_parameter["rosbridge_ip"] = rosbridge_ip
    default_parameter["rosbridge_port"] = rosbridge_port
    default_parameter["max_message_length"] = max_message_length
    default_parameter["listening_delay_s"] = listening_delay_s                  # maybe add socket timeouts..
    default_parameter["working_dir"] = working_dir
    default_parameter["logfile"] = ""

    # log messages to file
    def log(self,string=""):
        try:
            f = open(self.default_parameter["logfile"], "a")                                              # a -> append or create a new file
            try:
                f.write(str(string) + "\n")                                                 # Write string to file
            finally:
                f.close()
        except IOError:
            pass


    # initialize tcp2ws
    def __init__(self):
        self.useParameters()                                                    # import command line parameters
        self.default_parameter["logfile"]  = self.default_parameter["working_dir"]
        self.default_parameter["logfile"] += "/"
        self.default_parameter["logfile"] += logfile
        working_dir = self.default_parameter["working_dir"]
        f = open(self.default_parameter["logfile"], "w")                        # create new logfile (throw away old logfile)
        f.close()
        now = time.strftime("%Y-%M-%d %H:%M:%S")
        self.log(now + "    tcp2ws started")
        self.log()
        self.log(basic_instructions)                                            # log basic instructions for tcp2ws
        print basic_instructions
        #print self.default_parameter["logfile"]
        ws_socket = None                                                        # check if rosbridge-socket is available by connecting to it's websocket
        ws_uri =  "ws://" + str(self.default_parameter["rosbridge_ip"])         # generate the URI for rosbridge
        ws_uri += ":" + str(self.default_parameter["rosbridge_port"])
        try:                                                                    # open a websocket to the specified rosbridge to check if it is available
            ws_socket = create_connection(ws_uri)
            ws_socket.close()
            ws_socket = None
        except Exception, e:                                                    # if rosbridge is not available -> terminate tcp2ws
            self.log("rosbridge socket ["+ str(ws_uri) + "] is not available!")
	    sys.exit(0)
        self.listening_socket = socket.socket( socket.AF_INET,                  # create listening socket for accepting incoming tcp-connections from non-ros-clients
                                               socket.SOCK_STREAM )
        self.listening_socket.bind((self.default_parameter["listening_address"],
                                    int(self.default_parameter["listening_port"]) ))
        #self.listening_socket.settimeout(1)                                    # not used now, but keep in code for later
        #self.listening_socket.setblocking(0)                                   # not used now, but keep in code for later
        self.listening_socket.listen(1)
        threading.Thread.__init__(self)



    # tcp2ws destructor                                        
    # - should be reviewed and probably implemented in a "cleaner" way
    def __del__(self):
        for bridge in self.bridge_list:                                         #remove any existing bridge
           self.removeBridge(bridge)
        self.bridge_list = []                                                   # should be already empty now
        if self.listening_socket != None:                                       # close and remove listening socket for tcp-connections
            self.listening_socket.close()
            self.listening_socket = None

        filelist = [ f for f in os.listdir(self.default_parameter["working_dir"]) if f.endswith("tcp2ws.pid") ]
        for f in filelist:
            os.remove(f)

        now = time.strftime("%Y-%M-%d %H:%M:%S")
        self.log(now + "    tcp2ws closed")


    # parse commandline parameters
    # - following code could be implemented much better,
    #   but works good enough for now
    def useParameters(self):
        param_list = {}                                                         # dictionairy for parameters
        if (len(sys.argv)-1) % 2 == 0 and len(sys.argv) > 1:                    
            for i in range(len(sys.argv)/2):                                    # iterate through parameters and corresponding values
                key = sys.argv[(i*2)+1]
                value = sys.argv[(i*2)+2]
                if key[0] == "-" and key[1] == "-":                             # very basic check if we have a key beginning with "--"
                    key = key[2:]                                               # use word after "--" as parameter key
                param_list[key]= value                                          # set parameter value
            for key in param_list.keys():                                       # overwrite default parameters
                if key in self.default_parameter.keys():
                    self.default_parameter[key] = param_list[key]
                else:
                    msg  = "invalid parameter found: " + str(key)
                    msg += " " + str(param_list[key])
                    self.log(msg)                                                    # probably should terminate the programm or at least clean up parameters
                    #self.log " " + str(param_list[key])
        elif len(sys.argv) == 1:                                                # if call contains no parameters
            self.log("no parameters given.. using internal defaults")
        else:
            self.log("bad number of parameters given..")
            sys.exit(0)                                                         # terminate
        self.log()
        self.log("used settings:")                                                   # show results of parameter parsing
        self.log()
        for key in self.default_parameter.keys():
            self.log(str(key) + ": " + str(self.default_parameter[key]))
        self.log()


    # create a new bridge-object and append to bridge-list
    # - called on incoming tcp-connection
    def create_bridge(self, new_socket):
        new_bridge = bridgeObject.BridgeObject(self, new_socket,                # see bridgeObject.py for details
                        self.default_parameter["rosbridge_ip"],
                        int(self.default_parameter["rosbridge_port"]),
                        int(self.default_parameter["max_message_length"]),
                        float(self.default_parameter["listening_delay_s"]))
        self.bridge_list.append(new_bridge)                                     # put new bridge into bridge list
        now = time.strftime("%Y-%M-%d %H:%M:%S")                                # get string of current time
        msg  = now + "      client connected.        total clients: "
        msg += str(len(self.bridge_list))                                       # self.log number of existing bridges (connected clients)
        self.log(msg)


    # clean up after lost connections
    def removeBridge(self, bridge):
        try:
            bridge.destroyBridge()                                              # tell the bridge object to destroy itself
            self.bridge_list.remove(bridge)                                     # remove bridge object from list, maybe better check if it is None..
        except Exception, e:
            self.log(e)                                                              # comment this if no output of errors needed
            pass
        now = time.strftime("%Y-%M-%d %H:%M:%S")                                # get string of current time
        msg  = now + "      connection dropped.      total clients:"
        msg += str(len(self.bridge_list))
        self.log(msg)                                                                # self.log number of existing bridges (connected clients)


    # start the main programm
    def run(self):
        self.log()
        self.log("waiting for incoming tcp-connections...")
        try:
            while True:                                                         # loop forever and wait for incoming tcp-connections
                listening_list, xy , xx = select.select([self.listening_socket],# wait for I/O on listening socket and get list of new connections
                                                        [],
                                                        [],
                                                        listening_timeout)
                for newsocket in listening_list:                                # loop through new sockets
                    new_socket, addr = self.listening_socket.accept()           # accept and establish connection
                    self.create_bridge(new_socket)                              # call create_bridge
                time.sleep(self.default_parameter["listening_delay_s"])         # sleep for a while before checking for new connections again
        except Exception, e:
            self.log(e)                                                              # comment this if no output of errors needed
            pass



# ############################ end of class definition #########################


# this code runs after starting tcp2ws.py
if __name__ == "__main__":
    
    try:        
        TCP2WS().start()                                                        # create and start controller-object
    except Exception, e:                                                        # catch any Exception and show it,
        print e                                                                 # - probably the only place where universal Exception should be used
        print "TCP2WS-Bridge has stopped."

        # remove PID file in case the destructor was not called
        #print working_dir, "-file-"
        filelist = [ f for f in os.listdir(working_dir) if f.endswith("tcp2ws.pid") ]
        for f in filelist:
            os.remove(f)
