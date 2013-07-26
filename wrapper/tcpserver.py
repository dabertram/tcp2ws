import threading
import socket
import time



#TODO: - clean up Exception handling
#        * maybe not every Exception needs to break the connection
#TODO: - check if this can handle any "situation"
#TODO: - checking for connection close should be cleaner
#TODO: - check connection (do it the right way) before trying to send data



# class to listen on tcp-socket and pass data to the corresponding websocket
# - needs listening IP and port
# - needs wsclient object to pass incoming data from tcp-socket to websocket
class TCPserver(threading.Thread):
    max_message_length = None
    listening_delay_s = None
    wsclient = None
    tcp_socket = None
    parent_bridge = None
    stopped = False


    # initialize tcpserver object
    def __init__(self,                                                          # parameters get filled in by bridgeObject
                 newSocket,                                                     # the new connection that we got from our listening socket in TCP2WS
                 parentBridge,                                                  # parent bridge object to be able destroy it on errors
                 maxMessageLength = 1024,                                       # has default value, but gets overwritten anyways!
                 listeningDelayS = 0.1):                                        # has default value, but gets overwritten anyways!
        self.tcp_socket = newSocket
        self.parent_bridge = parentBridge
        self.max_message_length = maxMessageLength
        self.listening_delay_s = listeningDelayS
        threading.Thread.__init__(self)                                         # do thread initialization


    # tcpserver destructor
    def __del__(self):
        #self.parent_bridge.controller.log( "tcpserver-destructor called"                                    # debugging output
        self.tcp_socket.close()                                                 # close tcp-socket


    # allows to make wsclient object reachable from tcpserver since either
    #  tcpserver or wsclient need to spawn while no partner exists yet..
    def set_wsclient(self, new_wsclient):
        self.wsclient = new_wsclient                                            # just set wsclient object


    # send data to the corresponding tcp-socket
    # - gets called by wsclient on incoming data
    def sendData(self, data):
        try:
            self.tcp_socket.send(data)                                          # send data to non-ros-device
        except Exception, e:                                                    # if sending data fails: destroy parent bridge; this might be not always necessary
            self.parent_bridge.controller.log(e)                                # comment this if no output of errors needed
            pass                                                                # comment this if no output of errors is needed
            try:
                self.parent_bridge.controller.removeBridge(self.parent_bridge)  # destroy parent bridge
            except Exception, e:
                self.parent_bridge.controller.log(e)                            # comment this if no output of errors is needed
                #pass


    # start listening for incoming data on tcp-socket
    def run(self):
        while True and not self.stopped:                                        # loop and check for received data
            try:
                data = self.tcp_socket.recv(self.max_message_length)            # receive data
                if data == "":                                                  # check for connection-close; #TODO!
                    self.parent_bridge.destroyBridge()                          # if yes: tell parent_bridge to destroy itself
                else:
                    if self.wsclient != None:
                        self.wsclient.sendData(data)                            # pass data to wsclient
            except Exception, e:
                self.parent_bridge.controller.log(e)                            # comment this if no output of errors is needed
                
                try:
                    self.parent_bridge.controller.removeBridge(                 # on error: destroy parent bridge
                                                          self.parent_bridge)
                except Exception, e:
                    self.parent_bridge.controller.log(e)                        # comment this if no output of errors is needed
                    #pass
            time.sleep(self.listening_delay_s)                                  # put thread to sleep for a while to save cpu cycles
