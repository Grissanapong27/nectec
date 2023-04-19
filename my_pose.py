#!/usr/bin/env python3
#
# Copyright (c) 2021, NVIDIA CORPORATION. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

import sys
import argparse

from jetson_inference import poseNet
from jetson_utils import VideoSource, VideoOutput, Log

# parse the command line
parser = argparse.ArgumentParser(description="Run pose estimation DNN on a video/image stream.", 
                                 formatter_class=argparse.RawTextHelpFormatter, 
                                 epilog=poseNet.Usage() + videoSource.Usage() + videoOutput.Usage() + Log.Usage())

parser.add_argument("input", type=str, default="", nargs='?', help="URI of the input stream")
parser.add_argument("output", type=str, default="", nargs='?', help="URI of the output stream")
parser.add_argument("--network", type=str, default="resnet18-body", help="pre-trained model to load (see below for options)")
parser.add_argument("--overlay", type=str, default="links,keypoints", help="pose overlay flags (e.g. --overlay=links,keypoints)\nvalid combinations are:  'links', 'keypoints', 'boxes', 'none'")
parser.add_argument("--threshold", type=float, default=0.15, help="minimum detection threshold to use") 

try:
	args = parser.parse_known_args()[0]
except:
	print("")
	parser.print_help()
	sys.exit(0)

net = poseNet(args.network, sys.argv, args.threshold)


while True:
    img = input.Capture()
    if img is None: #timeout
        continue

    poses = net.Process(img, overlay=args.overlay)

    for pose in poses:
        left_wrist_index = pose.FindKeypoint('left_wrist')
        left_shoulder_index = pose.FindKeypoint('left_shoulder')
        left_elbow_index = pose.FindKeypoint('left_elbow')
        left_hip_index = pose.FindKeypoint('left_hip')
        left_ear_index = pose.FindKeypoint('left_ear')

        right_wrist_index = pose.FindKeypoint('right_wrist')
        right_shoulder_index = pose.FindKeypoint('right_shoulder')
        right_elbow_index = pose.FindKeypoint('right_elbow')
        right_hip_index = pose.FindKeypoint('right_hip')
        right_ear_index = pose.FindKeypoint('right_ear')

        neck_index = pose.Findkeypoint('neck')

        if left_wrist_index < 0 or left_shoulder_index < 0 or left_elbow_index < 0 or left_hip_index <0 or left_ear_index<0 or right_wrist_index< 0 or right_shoulder_index <0 or right_elbow_index< 0 or right_hip_index<0 or right_ear_index<0 or neck_index <0:
            continue
        
        left_wrist   =pose.Keypoints[left_wrist_index] 
        left_shoulde =pose.Keypoints[left_shoulder_index] 
        left_elbow   =pose.Keypoints[left_elbow_index]
        left_hip     =pose.Keypoints[left_hip_index]
        left_ear     =pose.Keypoints[left_ear_index]

        right_wrist   =pose.Keypoints[right_wrist_index] 
        right_shoulde =pose.Keypoints[right_shoulder_index] 
        right_elbow   =pose.Keypoints[right_elbow_index]
        right_hip     =pose.Keypoints[right_hip_index]
        right_ear     =pose.Keypoints[right_ear_index]

        neck = pose.Keypoints[neck_index]





        



