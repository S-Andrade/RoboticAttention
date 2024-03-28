import sys
from ElmoV2API import ElmoV2API
import time
if __name__ == "__main__":
    current_time = time.strftime("%Y%m%d_%H%M%S")
    robot_ip = "192.168.0.102"
    # API to communicate with RES request
    robot = ElmoV2API(robot_ip, debug = True)
    robot.set_screen(text="Hello World!")
    robot.enable_behavior(name="look_around", control = True) # make Elmo static
    robot.enable_behavior(name ="record_camera", control = False)
    robot.status()
    time.sleep(1)
    robot.start_video_recording()
    robot.start_recording()
    time.sleep(5) # time to record audio and video
    robot.status()
    robot.stop_video_recording() # record to False
    robot.stop_recording() # record to False
    time.sleep(2)   
    robot.status()  
    robot.enable_behavior(name="look_around", control = True) # make Elmo moving
    time.sleep(3)
    robot.status()
    robot.set_screen(text="Bye, world")
    # robot.reboot()