-------- SETUP -----------------------------------------------------------------
0:          <install python 2.7>
1:          sudo apt-get install python-pip
2:          sudo pip install websocket-client
3:          set websocket-port in code or use commandline parameters

-------- HOWTO -----------------------------------------------------------------
start rosbridge:        - roscore &
                        - rosrun rosbridge_server rosbridge.py &

use tcp2ws:		- ./tcp2ws start
			- ./tcp2ws stop
			- ./tcp2ws status

start ros-nodes and non-ros-clients:
                        - execute scripts in ros-scripts/ and non-ros-scripts/

-------- FILES -----------------------------------------------------------------
./wrapper/tcp2ws	- start-stop-script for tcp2ws
./wrapper/tcp2ws.log	- log-file (overwritten at start)
./wrapper/*.py	    	- python code of tcp2ws
./ros-scripts/	     	- ros examples to start publisher and listener nodes (ROS)
./non-ros-scripts/  	- non-ros examples to start publisher and listener clients (NON-ROS)
./experimental/     	- experimental test scripts (fragmentation, png compression, ..)
