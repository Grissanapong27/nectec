#!/usr/bin/env python3

import rospy
import smach
import smach_ros
import actionlib
import pyrealsense2 as rs
from actionlib_msgs.msg import *
from math import pow,sqrt,atan2,pi,radians
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from std_msgs.msg import String
from geometry_msgs.msg import Point,Pose,Quaternion,Twist
from nav_msgs.msg import Odometry
import time
#====================tooic node ======================================
x=0
y=0
theta=0

def posecallback(pose_message):
    global x
    global y,theta
    x = pose_message.pose.pose.position.x
    y = pose_message.pose.pose.position.y
    theta = pose_message.pose.pose.orientation

#===================== stop  ========================================

def stop():
    Velocity_publisher = rospy.Publisher('/cmd_vel',Twist,queue_size =10)
    vel_msg = Twist()
    #linear
    vel_msg.linear.x = 0
    #angular
    vel_msg.angular.z = 0
    Velocity_publisher.publish(vel_msg)


#====================== move ========================================

def move(speed, distance, Is_forward):
    Velocity_publisher = rospy.Publisher('/cmd_vel',Twist,queue_size =10)
    vel_msg = Twist()
    global x,y
    x0 = x
    y0 = y
    
    if(Is_forward):
        vel_msg.linear.x = abs(speed)
    else:
        vel_msg.linear.x = -abs(speed)
    
    vel_msg.linear.y = 0
    vel_msg.linear.z = 0
    vel_msg.angular.x = 0
    vel_msg.angular.y = 0
    vel_msg.angular.z = 0
    distance_moved = 0
    loop_rate = rospy.Rate(10)


    while True:
        rospy.loginfo("moves forwards")
        Velocity_publisher.publish(vel_msg)
        loop_rate.sleep()

        distance_moved = distance_moved + abs(0.5*sqrt(pow(x-x0,2)+pow(y-y0,2)))
        print(distance_moved)
        if not (distance_moved<distance):
            rospy.loginfo("reached")
            break

    vel_msg.linear.x = 0
    Velocity_publisher.publish(vel_msg)
#=======================  rotation  ==================================

def rotate(speed,angle,clockwise):
    Velocity_publisher = rospy.Publisher('/cmd_vel',Twist,queue_size = 10)
    vel_msg = Twist()
    global theta
    vel_msg = Twist()
    vel_msg.linear.x = 0
    vel_msg.linear.y = 0
    vel_msg.linear.z = 0 
    vel_msg.angular.x = 0
    vel_msg.angular.y = 0
    vel_msg.angular.z = 0

    theta0 = theta
    angular_speed = radians(abs(speed))
    if (clockwise):
        vel_msg.angular.z = -abs(angular_speed)
    else:
        vel_msg.angular.z = abs(angular_speed)

    angle_moved = 0
    loop_rate = rospy.Rate(10)

    t0 = rospy.Time.now().to_sec()

    while True:
        rospy.loginfo("Rotating")
        Velocity_publisher.publish(vel_msg)
    
        t1 = rospy.Time.now().to_sec()
        current_angle_degree = (t1-t0)*speed
        loop_rate.sleep()

        if (current_angle_degree>angle):
            rospy.loginfo("finished rotate")
            break

    vel_msg.angular.z = 0
    Velocity_publisher.publish(vel_msg)

##### not used in this code the follow node is in follow_node.py #######################
def follower(point):
    rotation_control = rospy.Publisher('/cmd_vel',Twist,queue_size=10)
    rotation = Twist()
    max_angular_speed = 0.5
    mid_angular_speed = 0.125
    min_angular_speed = 0.1
    if (point.x < 430) and (point.x > 0):
        rotation.angular.z = max_angular_speed
    elif (point.x < 540) and (point.x > 430):
        rotation.angular.z = mid_angular_speed
    elif (point.x < 600) and (point.x > 540):
        rotation.angular.z = min_angular_speed
    elif (point.x < 740) and (point.x > 680):
        rotation.angular.z = min_angular_speed
    elif (point.x < 850) and (point.x > 740):
        rotation.angular.z = min_angular_speed
    elif (point.x < 1280) and (point.x > 850):
        rotation.angular.z = min_angular_speed
    else:
        rotation.angular.z = 0
    rotation_control.publish(rotation)

#=======================  smach  =====================================

class sleep(smach.State):
    def __init__(self):
        stop()
        smach.State.__init__(self, outcomes=['forward','backward','hear_turn_left','hear_turn_right','Return_To_Base',"Go_To_Table","Go_To_Pole","follow"])
        rospy.Subscriber("/Speech2text",String,self.Voicecallback)
        self.voice_detector = ""
        #self.hand_detect = hand_topic

    def Voicecallback(self, data):
        self.voice_detector = data.data
    
    # set speech comand here
    def execute(self, userdata):
        rospy.loginfo('Executing state sleep')
        action_list = {"เดิน":"forward"
                        ,"ถอย หลัง":"backward"
                        ,"ถอย":"backward"
                        ,"TROY":"backward"
                        ,"ท้าย":"backward"
                        ,"เลี้ยว ซ้าย":"hear_turn_left"
                        ,"เลี้ยว ขวา":"hear_turn_right"
                        ,"กลับ":"Return_To_Base"
                        ,"เสา":"Go_To_Pole"
                        ,"เศร็า":"เ`Go_To_Pole"
                        ,"โต๊ะ":"Go_To_Tablee"
                        ,"ตาม มา":"follow"
                        }

        while not rospy.is_shutdown():
            if self.voice_detector in action_list:
                return action_list[self.voice_detector]
            else:
                pass
            #if self.voice_detector == "เดิน":
                #return 'forward'
            #elif self.voice_detector == "ถอย หลัง":
                #return 'backward'
            #elif self.voice_detector == "เลี้ยว ซ้าย":
                #return 'hear_turn_left'
            #elif self.voice_detector == "เลี้ยว ขวา":
                #return 'hear_turn_right'
            #elif self.voice_detector == "กลับ":
                #return 'Return_To_Base'
            #elif self.voice_detector == "เสา":
                #return 'Go_To_Pole'
            #elif self.voice_detector == "โต๊๊ะ":
                #return 'Go_To_Table'
            #else:
                #pass
class follow(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['stop_follow'])
        self.rotation = Twist()
        self.hand = String()
        self.vel = Twist()
        self.pub = rospy.Publisher('/cmd_vel',Twist,queue_size=10)
        vel_sub = rospy.Subscriber('/follow_status',Twist,self.vel_callback)
        rospy.Subscriber("/Speech2text",String,self.speech_callback)
        #human = rospy.Subscriber('/human_pose',Point,self.human_callback)
        # if want to run follow.py change topic maseege below to /rotation_vel
        #rotate_sub  = rospy.Subscriber('/rotation_vel',Twist,self.rotation_callback)
    #def rotation_callback(self,rotation_msgs):
        #self.rotation.angular.z = rotation_msgs.angular.z
    #def human_callback(self,human):
        #self.human_pose =  human
    def speech_callback(self,speech):
        self.speech = speech.data
    def vel_callback(self,data):
        self.vel =  data
    def execute(self,userdata):
        while True:
            self.pub.publish(self.vel)
            if self.speech == 'หยุด':
                return 'stop_follow'


class move_forward(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['finished_move_forward'])
        rospy.Subscriber("/Speech2text",String,self.callback)
        self.voice_detector = String()
    def callback(self, data):
        self.voice_detector = data.data

    def execute(self, userdata):
        rospy.loginfo('Executing state move forward')
        #you can ad just speed and distance by mode(speed,distance,forward?) if True = move foward,False = Move backward
        move(0.2,1,True)
        return 'finished_move_forward'

class move_backward(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['finished_move_backward'])
        rospy.Subscriber("/Speech2text",String,self.callback)
        self.voice_detector = String()
    def callback(self, data):
        self.voice_detector = data.data

    def execute(self, userdata):
        rospy.loginfo('Executing state move backward')
        #you can ad just speed and distance by mode(speed,distance,forward?) if True = move foward,False = Move backward
        move(0.2,1,False)
        #if self.voice_detector == 'หยุด':
            # return 'finished_move_backward'
        return 'finished_move_backward'
        #else:
            #pass


class turn_left(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['finished_turn_left'])
        rospy.Subscriber("/Speech2text",String,self.callback)
        self.voice_detector = String()
    def callback(self, data):
        self.voice_detector = data.data

    def execute(self, userdata):
        rospy.loginfo('Executing state turn left')
        #you can adjust angular speed and angle of rotation by ratate(speed,angle(degree),clockwise?)
        rotate(15,90,False)
            #if self.voice_detector == 'หยุด':
                # return 'finished_turn_left'
        return 'finished_turn_left'
            #else:
                #pass

class turn_right(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['finished_turn_right'])
        rospy.Subscriber("/Speech2text",String,self.callback)
        self.hand_detector = ""
    def callback(self, data):
        self.voice_detector = data.data

    def execute(self, userdata):
        rospy.loginfo('Executing state sleep')
        #while not rospy.is_shutdown():
        #you can adjust angular speed and angle of rotation by ratate(speed,angle(degree),clockwise?)
        rotate(15,90,True)
            #if self.voice_detector == 'หยุด':
                # return 'finished_turn_right'
        return 'finished_turn_right' 
            #else:
                #pass

#from This state below you can add location that what robot to navigate to
class GoToPosition(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['finished'])
        #location From Map to Base_link
        self.position = {'x':1.31 , 'y':0.78}
        self.quaternion = {'r1' : 0.000, 'r2' : 0.000, 'r3' :-0.183 , 'r4' : 0.983}

    def execute(self,userdata):
        rospy.loginfo('start go to location')
        self.navigator = GoToPose()
        self.success = self.navigator.goto(self.position,self.quaternion)
        #rospy.loginfo("Go to ($s,%s) position",self.position['x'],self.position['y'])
        if self.success:
            rospy.loginfo('reach loaction')
            return 'finished'

class GoToTable(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['finished'])
        self.position = {'x':3.489 , 'y':4.481}
        self.quaternion = {'r1' : -0.000, 'r2' : -0.000, 'r3' :0.610 , 'r4' : 0.792}

    def execute(self,userdata):
        rospy.loginfo('start go to location')
        self.navigator = GoToPose()
        self.success = self.navigator.goto(self.position,self.quaternion)
        #rospy.loginfo("Go to ($s,%s) position",self.position['x'],self.position['y'])
        if self.success:
            rospy.loginfo('reach loaction : Table')
            return 'finished'

class GoToPole(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['finished'])
        self.position = {'x': 0.671 , 'y':2.851}
        self.quaternion = {'r1' : 0.000, 'r2' : 0.000, 'r3' :0.262 ,'r4' : 0.965}

    def execute(self,userdata):
        rospy.loginfo('start go to location')
        self.navigator = GoToPose()
        self.success = self.navigator.goto(self.position,self.quaternion)
        #rospy.loginfo("Go to ($s,%s) position",self.position['x'],self.position['y'])
        if self.success:
            rospy.loginfo('reach loaction : Pole')
            return 'finished'


def main():
    rospy.init_node('Voice_control')

    sm = smach.StateMachine(outcomes=['---finish---'])
    with sm:
        smach.StateMachine.add('sleep',sleep(),transitions={'forward':'move_forward'
                                                            ,'backward':'move_backward'
                                                            ,'hear_turn_left':'turn_left'
                                                            ,'hear_turn_right':'turn_right'
                                                            ,'Return_To_Base':'GoToPositon'
                                                            ,'Go_To_Pole':'GoToPole'
                                                            ,'Go_To_Table':'GoToTable'
                                                            ,'follow':'follow'})
        smach.StateMachine.add('move_forward',move_forward(),transitions={'finished_move_forward':'sleep'})
        smach.StateMachine.add('move_backward',move_backward(),transitions={'finished_move_backward':'sleep'})
        smach.StateMachine.add('turn_left',turn_left(),transitions={'finished_turn_left':'sleep'})
        smach.StateMachine.add('turn_right',turn_right(),transitions={'finished_turn_right':'sleep'})
        smach.StateMachine.add('GoToPositon',GoToPosition(),transitions={'finished':'sleep'})
        smach.StateMachine.add('GoToTable',GoToTable(),transitions={'finished':'sleep'})
        smach.StateMachine.add('GoToPole',GoToPole(),transitions={'finished':'sleep'})
        smach.StateMachine.add('follow',follow(),transitions={'stop_follow':'sleep'})

    sis = smach_ros.IntrospectionServer('speech_control',sm ,'/speech')
    sis.start()
        
    outcome = sm.execute()
#================= Go To Specifi Location ===========================

class GoToPose:
    def __init__(self):
        self.goal_sent = False
        rospy.on_shutdown(self.shutdown)
        self.move_base = actionlib.SimpleActionClient("move_base",MoveBaseAction)
        rospy.loginfo("wait for the action sever to come up")

        #ALLOW up to 5 seconds for the action server to come up
        self.move_base.wait_for_server(rospy.Duration(5))
    
    def goto(self, pos ,quat):
        self.goal_sent = True
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = 'map'
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose = Pose(Point(pos['x'],pos['y'],0.000),
                                     Quaternion(quat['r1'],quat['r2'],quat['r3'],quat['r4']))

        #star moving
        self.move_base.send_goal(goal)
        success = self.move_base.wait_for_result(rospy.Duration(60))
        state = self.move_base.get_state()
        result = False

        if success and state == GoalStatus.SUCCEEDED:
            result = True
        else:
            self.move_base.cancel_goal()

        self.goal_sent = False
        return result
    
    def shutdown(self):
        #if self.goal_sent:
            #self.move_base.cancel_goal()
        rospy.loginfo("stop")
        rospy.sleep(1)

#======================================================================
if __name__ == '__main__':  
    pose_subscriber = rospy.Subscriber('/odom',Odometry,posecallback)
    time.sleep(2)
    main()
