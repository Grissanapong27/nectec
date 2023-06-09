#!/usr/bin/env python3

import rospy
import smach
import smach_ros
from math import pow,sqrt,atan2,pi
from geometry_msgs.msg import Point,Pose,Quaternion,Twist
from nav_msgs.msg import Odometry

#Humanpose = rospy.Subscriber('',Point,)

#define Roatation speed
max_rotation = 0.3
mid_rotation = 0.1
min_rotation = 0.05
#define velocity
max_vel = 0.4
mid_vel = 0.3
min_vel = 0.2


def move(distance):
    if distance > 5000:
        return max_vel
    elif distance > 1500 and distance < 3000:
        return mid_vel
    elif distance > 1000 and distance < 1500:
        return min_vel
    elif distance > 800  and distance < 1000:
        return -min_vel
    elif distance < 800:
        return 0
    else:
        return 0

class follow:

    def __init__(self):
        rospy.init_node('follow_control',anonymous = True)
        global rotation_control  
        rotation_control = rospy.Publisher('/follow_status',Twist,queue_size=10)
        pose_sub = rospy.Subscriber('/human_pose',Point,self.Rotation)
        dist_sub = rospy.Subscriber('/human_distance',Point,self.distace_callback)
        self.distance = 0
        rospy.spin()

    def distace_callback(self,data):
        self.distance = data.x

    #1280 x 720 is size of image use to define location of human in code below
    def Rotation(self,point):
        global rotation_control
        rotation = Twist()
        if (point.x <430) and (point.x > 0):
            rotation.angular.z = max_rotation
            rotation.linear.x = move(self.distance)
        elif (point.x <540) and (point.x > 430):
            rotation.angular.z = mid_rotation
            rotation.linear.x = move(self.distance)
        elif (point.x <600) and (point.x > 540):
            rotation.angular.z = min_rotation
            rotation.linear.x = move(self.distance)
        elif (point.x <740) and (point.x > 680):
            rotation.angular.z = -min_rotation
            rotation.linear.x = move(self.distance)
        elif (point.x <850) and (point.x > 740):
            rotation.angular.z = -mid_rotation
            rotation.linear.x = move(self.distance)
        elif (point.x <1280) and (point.x > 850):
            rotation.angular.z = -max_rotation
            rotation.linear.x = move(self.distance)
        else:
            rotation.angular.z = 0
            rotation.linear.x = move(self.distance)

        rotation_control.publish(rotation)

if __name__ == '__main__':
    start = follow()



