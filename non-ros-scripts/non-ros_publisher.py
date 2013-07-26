#!/usr/bin/python
import socket
import time

# ROS imports
import roslib
#roslib.load_manifest('beginner_tutorials')
import rospy

#connect to the socket
host1_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host1_sock.settimeout(1)
host1_sock.connect(('localhost', 9095))
#host1_sock.send('raw\r\n\r\n')

#tell the socket what topics should be subscribed (i.e. camera voltage)
#host1_sock.send('\x00{"receiver":"/rosbridge/subscribe","msg":["/#flexible_joint_states",-1,"sensor_msgs/JointState"]}\xff')

#advertise topic
advertise_message= """{"op": "advertise", "topic": "nonroschatter", "type": "std_msgs/String"}"""
host1_sock.send(str(advertise_message))
time.sleep(1)
try:
    while True:
        try:
            message = """{"op": "publish", "topic": "nonroschatter", "msg": {"data": "Hello World"}}"""
            print "sending: ", str(message)
            host1_sock.send(str(message))
            #incoming = host1_sock.recv(1024)
            #incoming = incoming[1:len(incoming)-1]
            #incoming contains the messages on the subscribed topics
            
            time.sleep(1)
        except Exception, e:
            print e
            print "got no message within timeout"

    #    #publish something (i.e. data from sps like odometry)
    #    host1_sock.send('\x00{"receiver":"/bridge_topic", "msg":{"data": 42}, "type":"std_msgs/#Int32"}\xff')
    #    host1_sock.send("""{op: 'publish', topic:'/chatter', msg:'rosbridge over tcp-socket'}""")
        time.sleep(0.1)
except KeyboardInterrupt:
    print "non-ros-publisher aborted"
