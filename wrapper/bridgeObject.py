import tcpserver
import wsclient



#TODO: - implement cleaner way to stop and remove bridge and tcp- and websockets!



# class to manage connections between tcp- and websockets
class BridgeObject():
    wsclient = None
    tcpserver = None
    controller = None
    parent_bridge = None
    rosbridge_ip = None
    rosbridge_port = None
    max_message_length = None
    listening_delay_s = None
    destroyed = False


    # initialize the bridge object
    def __init__(self,                                                          # parameters get filled in by tcp2ws.py
                 controller,
                 tcpSocket,
                 rosbridgeIP,
                 rosbridgePort,
                 maxMessageLength = 1024,
                 listeningDelayS = 0.1):
        self.controller = controller                                            # the parent object (TCP2WS)
        self.rosbridge_ip = rosbridgeIP
        self.rosbridge_port = rosbridgePort
        self.max_message_length = maxMessageLength
        self.listening_delay_s = listeningDelayS
        self.tcpserver = tcpserver.TCPserver(                                   # create tcpserver-object
                                             tcpSocket,                         # the new connection that we got from our listening socket in TCP2WS
                                             self,                              # make bridge object (this object) reachable from tcpserver-object to destroy it on errors
                                             maxMessageLength = maxMessageLength,
                                             listeningDelayS = listeningDelayS)        
        self.wsclient = wsclient.WSclient(self.rosbridge_ip,                    # create wsclient-object
                                          self.rosbridge_port,
                                          self.tcpserver,                       # make tcp-server object reachable from wsclient
                                          self.max_message_length,
                                          self.listening_delay_s,
                                          self)                                 # make bridge object reachable from wsclient-object to destroy it on errors
        self.tcpserver.set_wsclient(self.wsclient)                              # set wsclient in tcpserver (to pass data from tcp- to websocket)
                                                                                # - (solves kind of chicken-egg problem, lol)
        self.tcpserver.start()                                                  # start tcpserver
        self.wsclient.start()                                                   # start wsclient


    # bridgeObject destructor                                        
    # - should be reviewed and probably implemented in a "cleaner" way
    def __del__(self):
        if not self.destroyed:                                                  # if not yet destroyed (sockets might be still alive..)
            #self.controller.log( "bridge: not destroyed, destroying now.."                    # debugging output
            self.destroyBridge()                                                # destroy the bridgeObject


    # destroy the bridge
    # .. and corresponding tcpserver- and wsclient objects
    def destroyBridge(self):
        if self.wsclient != None:                                               # if wsclient object still exists
            try:
                self.wsclient.stopped = True                                    # should be unnecessary! ..allows to get out of websocket listening loop
                self.wsclient.__del__()                                         # call destructor for wsclient object (maybe use another method for that..)
            except Exception, e:
                self.controller.log(e)                                          # comment this if no output of errors needed
                #pass
            self.wsclient = None                                                # should be already "None";  maybe move this line into try-catch block above or remove
        if self.tcpserver != None:                                              # if tcpserver object still exists
            try:
                self.tcpserver.stopped = True                                   # should be unnecessary! ..allows to get out of tcpserver listening loop
                self.tcpserver.__del__()                                        # call destructor for tcpserver object (maybe use another method for that..)
            except Exception, e:
                self.controller.log(e)                                          # comment this if no output of errors needed
                #pass
            self.tcpserver = None                                               # should be already "None";  maybe move this line into try-catch block above or remove
        self.destroyed = True                                                   # mark bridge object itself as destroyed; should be in try-catch block above..


        