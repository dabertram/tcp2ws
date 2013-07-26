#!/usr/bin/python

# example script for fragmented messages:
# - op:         fragment
# - id:         generate message ID to identify which fragments belong to a message
# - data:       split full message into parts (just split the string..)
# - num:        generate 'fragment ID' for each fragment (in order to reconstruct the full message)
# - total:      defines how many fragments belong to a fragmented message
#
#

import re

import socket
import time

from random import randint
import sys

# ROS imports
import roslib
#roslib.load_manifest('beginner_tutorials')
import rospy


import json




#  fragmentation example #######################################################
def list_of_fragments():
    # generate full_message_data
    message_length = 50                                     # bytes / letters / ..
    full_message_data = ""
    for i in range(0,message_length):
        full_message_data += chr(randint(0,25)+65)               # append random capital letter to string
    print full_message_data


    # generate full message with full data and headers
    full_message_begin = '"op": "publish", "topic": "nonrosfragmentedchatter", "msg": {"data": "'
    full_message_end   = '"}'
    full_message = full_message_begin + full_message_data + full_message_end

    

    #full_message = full_message_data

    print "full_message:"
    print full_message

    full_message = full_message.replace('"', '\"')

    # now generate fragments of this huge message


    # generate message id
    message_id = randint(0,64000)


    #generate list of fragments
    fragment_length = 5
    fragments = []                                          # create empty fragment list
    cursor = 0
    while cursor < len(full_message):
        fragment_begin = cursor
        if len(full_message) < cursor + fragment_length:
            fragment_end = len(full_message)
            cursor = len(full_message)
        else:
            fragment_end = cursor + fragment_length
            cursor += fragment_length
        fragment = full_message[fragment_begin:fragment_end]
        fragments.append(fragment)



    # generate list of fragmented messages
    fragmented_messages_list = []
    for count, fragment in enumerate(fragments):                # iterate through list and have index counter
        fragmented_message =  '{"op": "fragment", '                               # op-code
        fragmented_message += '"id": "' + str(message_id) + '", '                # message-id

        fragmented_message += '"data": "' + fragment + '", '               # fragment-data
        fragmented_message += '"num": ' + str(count) + ', '                    # fragment-id
        fragmented_message += '"total": ' + str(len(fragments)) +'}'         # total-fragments

        #fragmented_message = fragmented_message.replace('"', "'")


        #fragmented_message = fragmented_message.replace('"', '\'')
        fragmented_messages_list.append(fragmented_message)

    #####################################################
    # test json.loads(msg) function on recombined string
#    import json
#
#    teststring = ""
    for fragm in fragmented_messages_list:
#        #print "fragment:"
        print fragm
#        #print
#        json_fragm = json.loads(fragm)
#        #print "json.loads(fragment) passed"
#
#        #print "json_fragm[\"data\"]:", json_fragm["data"]
#
#        teststring += json_fragm["data"]

    
#    print "full message:"
#    print full_message
#    print
#    json.loads(full_message)
#    print "json.loads(full_message) passed"
#
#    print "teststring:"
#    print teststring
#    print
#    json.loads(teststring)

#    teststring = teststring.replace("'", '\"')
#
#    teststring = teststring
#    print "re.escaped teststring:"
#    print teststring
#    print
#    json.loads(teststring)
#    print "re.escape(teststring)"
#
#    print "json.loads(teststring) passed"
#    print "json.loads(teststring) passed"
#    print "json.loads() finished.. ..exiting"
#
#    import sys
#    sys.exit(1)
    #####################################################
        
    

    return fragmented_messages_list


## fragmentation example end ###################################################




#connect to the socket
host1_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host1_sock.settimeout(1)
host1_sock.connect(('localhost', 9095))
#host1_sock.send('raw\r\n\r\n')
#tell the socket what topics should be subscribed (i.e. camera voltage)
#host1_sock.send('\x00{"receiver":"/rosbridge/subscribe","msg":["/#flexible_joint_states",-1,"sensor_msgs/JointState"]}\xff')


#advertise topic
advertise_message= '{"op": "advertise", "topic": "nonrosfragmentedchatter", "type": "std_msgs/String"}'
print "advertised topic:", advertise_message
host1_sock.send(str(advertise_message))
time.sleep(1)
try:
    while True:
        try:

            #connect to the socket
#            host1_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#            host1_sock.settimeout(1)
#            host1_sock.connect(('localhost', 9095))
            #host1_sock.send('raw\r\n\r\n')
            #tell the socket what topics should be subscribed (i.e. camera voltage)
            #host1_sock.send('\x00{"receiver":"/rosbridge/subscribe","msg":["/#flexible_joint_states",-1,"sensor_msgs/JointState"]}\xff')


            # create new big message to avoid duplicate IDs
            for message in list_of_fragments():
                #print "replacing: ", str(message)

                
                print "sending:   ", str(message)

                host1_sock.send(str(message))

                json.loads(str(message))


                #incoming = host1_sock.recv(1024)
                #incoming = incoming[1:len(incoming)-1]
                #incoming contains the messages on the subscribed topics
            
                time.sleep(0.2)

        except Exception, e:
            print e
            print "got no message within timeout"

    #    #publish something (i.e. data from sps like odometry)
    #    host1_sock.send('\x00{"receiver":"/bridge_topic", "msg":{"data": 42}, "type":"std_msgs/#Int32"}\xff')
    #    host1_sock.send("""{op: 'publish', topic:'/chatter', msg:'rosbridge over tcp-socket'}""")
        time.sleep(2)
except KeyboardInterrupt:
    print "non-ros-publisher aborted"
