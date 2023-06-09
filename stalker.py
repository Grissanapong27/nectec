#!/usr/bin/env python3

import rospy
import smach
import smach_ros
from math import pow,sqrt,atan2,pi
from geometry_msgs.msg import Point,Pose,Quaternion,Twist
from nav_msgs.msg import Odometry

#Humanpose = rospy.Subscriber('',Point,)
max_rotation = 0.3
mid_rotation = 0.1
min_rotation = 0.05

max_vel = 0.4
mid_vel = 0.2
min_vel = 0.1
class follow:
    def __init__(self):
        rospy.init_node('Rotation_control',anonymous = True)
        global rotation_control  
        rotation_control = rospy.Publisher('/cmd_vel',Twist,queue_size=10)
        pose_sub = rospy.Subscriber('/human_pose',Point,self.Rotation)
        dist_sub = rospy.Subscriber('/human_distance',Point,self.distace_callback)
        self.distance = 0
        rospy.spin()
    def distace_callback(self,data):
        self.distance = data.x
    def Rotation(self,point):
        global rotation_control
        rotation = Twist()
        if (point.x <430) and (point.x > 0):
            rotation.angular.z = max_rotation
            if self.distance > 1500:
                rotation.linear.x = max_vel
            elif self.distance > 900 and self.distance < 1500:
                rotation.linear.x = mid_vel
            elif self.distance > 700 and self.distance <900:
                rotation.linear.x = min_vel
            else:
                rotation.linear.x = 0
        elif (point.x <540) and (point.x > 430):
            rotation.angular.z = mid_rotation
            if self.distance > 1500:
                rotation.linear.x = max_vel
            elif self.distance > 900 and self.distance < 1500:
                rotation.linear.x = mid_vel
            elif self.distance > 700 and self.distance <900:
                rotation.linear.x = min_vel
            else:
                rotation.linear.x = 0
        elif (point.x <600) and (point.x > 540):
            rotation.angular.z = min_rotation
            if self.distance > 1500:
                rotation.linear.x = max_vel
            elif self.distance > 900 and self.distance < 1500:
                rotation.linear.x = mid_vel
            elif self.distance > 700 and self.distance <900:
                rotation.linear.x = min_vel
            else:
                rotation.linear.x = 0
        elif (point.x <740) and (point.x > 680):
            rotation.angular.z = -min_rotation
            if self.distance > 1500:
                rotation.linear.x = max_vel
            elif self.distance > 900 and self.distance < 1500:
                rotation.linear.x = mid_vel
            elif self.distance > 700 and self.distance <900:
                rotation.linear.x = min_vel
            else:
                rotation.linear.x = 0
        elif (point.x <850) and (point.x > 740):
            rotation.angular.z = -mid_rotation
            if self.distance > 1500:
                rotation.linear.x = max_vel
            elif self.distance > 900 and self.distance < 1500:
                rotation.linear.x = mid_vel
            elif self.distance > 700 and self.distance <900:
                rotation.linear.x = min_vel
            else:
                rotation.linear.x = 0
        elif (point.x <1280) and (point.x > 850):
            rotation.angular.z = -max_rotation
            if self.distance > 1500:
                rotation.linear.x = max_vel
            elif self.distance > 900 and self.distance < 1500:
                rotation.linear.x = mid_vel
            elif self.distance > 700 and self.distance <900:
                rotation.linear.x = min_vel
            else:
                rotation.linear.x = 0
        else:
            rotation.angular.z = 0
            if self.distance > 3000:
                rotation.linear.x = max_vel
            elif self.distance > 1500 and self.distance < 3000:
                rotation.linear.x = mid_vel
            elif self.distance > 700 and self.distance <1500:
                rotation.linear.x = min_vel
            else:
                rotation.linear.x = 0

        rotation_control.publish(rotation)

#def posecallback(odom):

if __name__ == '__main__':
    start = follow()



