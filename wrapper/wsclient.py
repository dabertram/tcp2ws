from websocket import create_connection
import threading
import time



#TODO: - clean up Exception handling
#        * maybe not every Exception needs to break the connection
#TODO: - check if this can handle any "situation"
#TODO: - checking for connection close should be cleaner
#TODO: - check connection before trying to send data



# class to listen on websocket and pass data to the corresponding tcp-socket
# - needs rosbridge IP and port to open the connection to rosbridge
# - needs tcpserver object to pass data from websocket to tcp-socket
class WSclient(threading.Thread):
    tcpserver = None
    ws_socket = None
    parent_bridge = None
    controller = None
    rosbridge_ip = "localhost"                                                  # gets overwritten on __init__
    rosbridge_port = 9090                                                       # gets overwritten on __init__
    max_message_length = None
    listening_delay_s = None
    ws_uri = None
    stopped = False


    # initialize wsclient object
    def __init__(self,
                 rosbridgeIP,
                 rosbridgePort,
                 tcpServer,                                                     # make tcp-server object reachable from wsclient
                 maxMessageLength = 1024,                                       # has default value, but gets overwritten anyways!
                 listeningDelayS = 0.1,                                         # has default value, but gets overwritten anyways!
                 parent_bridge=None):                                           # parent bridge object to be able destroy it on errors
        self.tcpserver = tcpServer
        self.rosbridge_ip = rosbridgeIP
        self.rosbridge_port = rosbridgePort
        self.max_message_length = maxMessageLength
        self.listening_delay_s = listeningDelayS
        self.parent_bridge = parent_bridge
        self.ws_uri =  "ws://" + str(self.rosbridge_ip)
        self.ws_uri += ":" + str(self.rosbridge_port)
        try:
            self.ws_socket = create_connection(self.ws_uri)                     # try to connect to rosbridge
        except Exception, e:
            #self.parent_bridge.controller.log( "wsclient: cannot create connection to ros-bridge", e        # debugging output
            pass
        threading.Thread.__init__(self)                                         # do thread initialization


    # wsclient destructor
    def __del__(self):
        #self.parent_bridge.controller.log( "wsclient-destructor called"        # debugging output
        self.ws_socket.close()                                                  # close websocket


    # send data to the corresponding websocket
    # - gets called by wsclient on incoming data
    def sendData(self, data):
        try:
            self.ws_socket.send(data)                                           # send data to rosbridge
        except Exception, e:                                                    # if sending data fails: destroy parent bridge; this might be not always necessary
            #self.parent_bridge.controller.log( "wsclient: error trying to send data to websocket..", e      # debugging output
            try:
                self.parent_bridge.controller.removeBridge(self.parent_bridge)  # destroy parent-bridge object
            except Exception, e:
                self.parent_bridge.controller.log(e)                                                         # comment this if no output of errors needed
                #pass


    # start listening for incoming data on websocket
    def run(self):
        while True and not self.stopped:
            try:
                data = self.ws_socket.recv()
                # maybe add check for connection close here..                   # check for connection-close; #TODO!
                self.tcpserver.sendData(data)                                   # pass data to tcpserver
            except Exception, e:                                                # this catches both, send and receive errors.. implement in a better way!
                self.parent_bridge.controller.log(e)                                                         # comment this if no output of errors needed
                if (self.parent_bridge != None                                  # needed to avoid loops when trying to destroy bridges; compare with tcpserver; #TODO!
                   and self.parent_bridge.controller) != None:
                    #self.parent_bridge.controller.log( self.parent_bridge.controller
                    try:
                         self.parent_bridge.controller.removeBridge(            # destroy
                                                            self.parent_bridge)
                    except Exception, e:
                        self.parent_bridge.controller.log(e)                                                 # comment this if no output of errors needed
                        #self.parent_bridge.controller.log( "wsclient: bridge was already removed"           # debugging output
                        #pass
            time.sleep(self.listening_delay_s)