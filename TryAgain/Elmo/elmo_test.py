import sys
from asyncio import sleep
import time

from ElmoV2API import ElmoV2API

# Main function
if __name__ == '__main__':
    # We will pass the robot's IP in ter terminal as an argument
    # Note that you need to connect to the app first to discover the IP of the robot
    robot_ip = "192.168.0.102"

    # Initiate the API to communicate with RES request with the robots
    robot = ElmoV2API(robot_ip, debug=True)

    # Check the robot is connected and its current status You can use this command to get information about the
    # battery, what behaviors are active, which files are inside the robot, etc.
    print(robot.status())

    robot.enable_behavior(name="look_around", control = True)
    robot.set_pan(-40)
    robot.speak("Olá, eu falo português", "pt")
    robot.set_tilt(-8)
    
    #robot.reboot()

