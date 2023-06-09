#!/usr/bin/env python3.8

import sys
import argparse
import rospy
import numpy as np
import cv2
import pyrealsense2 as rs
from cv_bridge import CvBridge
from geometry_msgs.msg import Point
from sensor_msgs.msg import Image
from jetson_inference import detectNet
from jetson_utils import videoSource, videoOutput, Log, cudaFromNumpy

# parse the command line
parser = argparse.ArgumentParser(description="Locate objects in a live camera stream using an object detection DNN.", 
                                 formatter_class=argparse.RawTextHelpFormatter, 
                                 epilog=detectNet.Usage() + videoSource.Usage() + videoOutput.Usage() + Log.Usage())

parser.add_argument("input", type=str, default="/dev/vide0", nargs='?', help="URI of the input stream")
parser.add_argument("output", type=str, default="", nargs='?', help="URI of the output stream")
parser.add_argument("--network", type=str, default="ssd-mobilenet-v2", help="pre-trained model to load (see below for options)")
parser.add_argument("--overlay", type=str, default="box,labels,conf", help="detection overlay flags (e.g. --overlay=box,labels,conf)\nvalid combinations are:  'box', 'labels', 'conf', 'none'")
parser.add_argument("--threshold", type=float, default=0.5, help="minimum detection threshold to use") 

is_headless = ["--headless"] if sys.argv[0].find('console.py') != -1 else [""]

try:
	args = parser.parse_known_args()[0]
except:
	print("")
	parser.print_help()
	sys.exit(0)

ช
# load the object detection network
net = detectNet(args.network, sys.argv, args.threshold)

# note: to hard-code the paths to load a model, the following API can be used:
#
# net = detectNet(model="model/ssd-mobilenet.onnx", labels="model/labels.txt", 
#                 input_blob="input_0", output_cvg="scores", output_bbox="boxes", 
#                 threshold=args.threshold)

ช
class Det():
    def __init__(self):
        self.output = videoOutput(args.output, argv=sys.argv+is_headless)
        self.pub = rospy.Publisher('/human_pose',Point,queue_size = 10)
        self.depthpub = rospy.Publisher('/human_distance',Point,queue_size =10)
        self.depth = rospy.Subscriber('/camera/depth/image_rect_raw',Image,self.depthcam)
        self.image = rospy.Subscriber('/camera/color/image_raw',Image,self.camera)
        self.bridge = CvBridge()
        self.minDepth = Point()
    def depthcam(self,depth_msgs):
        self.depth_img = self.bridge.imgmsg_to_cv2(depth_msgs,desired_encoding='passthrough')
        width= 1280
        height = 720
        dim = (width,height)
        self.depth_img = cv2.resize(self.depth_img,dim,interpolation = cv2.INTER_AREA)

    def camera(self,img_msgs):
        try:
            img = self.bridge.imgmsg_to_cv2(img_msgs,"bgr8")
            width = 1280
            height = 720
            dim = (width,height)
            img = cv2.resize(img, dim,interpolation = cv2.INTER_AREA)
            cuda_img = cudaFromNumpy(img)
            
            # detect objects in the image (with overlay)
            detections = net.Detect(cuda_img, overlay=args.overlay)

            # print the detections
            print("detected {:d} objects in image".format(len(detections)))

            for detection in detections:
                if detection.ClassID == 1:
                    print(detection.ClassID)
                    point = Point()
                    point.x = detection.Center[0]
                    point.y = detection.Center[1]
                    print(point.x)
                    print(point.y)
                    print("left :",detection.Left)
                    print("Right :",detection.Right)
                    min_depth = Point()
                    #min_depth.x = 2
                    #print(int(self.depth_img[360,640]))
                    #min_depth.x = int(self.depth_img[360,640])
                    min_depth.x = 300
                    x_scan = None
                    for x_scan in range(int(detection.Left),int(detection.Right)):
                        if x_scan > 720:
                            x_scan = 700
                        depth = int(self.depth_img[int(x_scan),int(point.y)])
                        #print(int(self.depth_img[int(x_scan),int(point.y)]))
                        if (depth > min_depth.x):
                            min_depth.x = depth

                    self.depthpub.publish(min_depth)
                    self.pub.publish(point)

            # render the image
            self.output.Render(cuda_img)

            # update the title bar
            self.output.SetStatus("{:s} | Network {:.0f} FPS".format(args.network, net.GetNetworkFPS()))

            # exit on input/output EOS
        except Exception as e:
            rospy.loginfo('Error process image: {}'.format(e))
def main():
    img = Det()
    rospy.init_node('Human_detection',anonymous = True)
    try:
        rospy.spin()
    except KeyboardInterrupt:
        print("shutting down")
if __name__ == '__main__':
    main()

