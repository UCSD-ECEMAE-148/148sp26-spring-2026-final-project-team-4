#!/usr/bin/env python

# Copyright (c) 2012, Tang Tiong Yew
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the Willow Garage, Inc. nor the names of its
#      contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import rclpy
from rclpy.node import Node
import serial
import math
import sys
import numpy as np
import time

#from time import time
from sensor_msgs.msg import Imu
from sensor_msgs.msg import MagneticField
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from rcl_interfaces.msg import SetParametersResult
from tf_transformations import quaternion_from_euler

DEGREES_2_RAD = math.pi/180.0
MIN_YAW_CALIBRATION = -10
MAX_YAW_CALIBRATION = 10

class RazorImuNode(Node):
    def __init__(self):
        super().__init__('razor_imu_node')
        self.imu_pub_ = self.create_publisher(Imu, 'imu', rclpy.qos.qos_profile_sensor_data)
        self.diag_pub_ = self.create_publisher(DiagnosticArray, 'diagnostics', rclpy.qos.qos_profile_sensor_data)

        self.declare_parameter('imu_yaw_calibration', 0.0)
        self.imu_yaw_calib_ = self.get_parameter('imu_yaw_calibration').value

        self.declare_parameter('orientation_covariance', 
            [0.0025 , 0.0 , 0.0,
            0.0, 0.0025, 0.0,
            0.0, 0.0, 0.0025]
        )
        self.orientation_covariance_ = self.get_parameter('orientation_covariance').value

        self.declare_parameter('angular_velocity_covariance', 
            [0.02, 0.0 , 0.0,
            0.0 , 0.02, 0.0,
            0.0 , 0.0 , 0.02]
        )
        self.angular_velocity_covariance_ = self.get_parameter('angular_velocity_covariance').value

        self.declare_parameter('linear_acceleration_covariance',
            [0.04 , 0.0 , 0.0,
            0.0 , 0.04, 0.0,
            0.0 , 0.0 , 0.04]
        )
        self.linear_acceleration_covariance_ = self.get_parameter('linear_acceleration_covariance').value

        self.declare_parameter("port", "/dev/ttyUSB0")
        self.port_ = self.get_parameter('port').value

        self.declare_parameter("frame_id", "base_imu_link")
        self.frame_id_ = self.get_parameter('frame_id').value

        self.declare_parameter("accel_x_min", -250.0)
        self.accel_x_min_ = self.get_parameter('accel_x_min').value

        self.declare_parameter("accel_x_max", 250.0)
        self.accel_x_max_ = self.get_parameter('accel_x_max').value

        self.declare_parameter("accel_y_min", -250.0)
        self.accel_y_min_ = self.get_parameter('accel_y_min').value

        self.declare_parameter("accel_y_max", 250.0)
        self.accel_y_max_ = self.get_parameter('accel_y_max').value

        self.declare_parameter("accel_z_min", -250.0)
        self.accel_z_min_ = self.get_parameter('accel_z_min').value

        self.declare_parameter("accel_z_max", 250.0)
        self.accel_z_max_ = self.get_parameter('accel_z_max').value

        self.declare_parameter("magn_x_min", -600.0)
        self.magn_x_min_ = self.get_parameter('magn_x_min').value

        self.declare_parameter("magn_x_max", 600.0)
        self.magn_x_max_ = self.get_parameter('magn_x_max').value

        self.declare_parameter("magn_y_min", -600.0)
        self.magn_y_min_ = self.get_parameter('magn_y_min').value

        self.declare_parameter("magn_y_max", 600.0)
        self.magn_y_max_ = self.get_parameter('magn_y_max').value

        self.declare_parameter("magn_z_min", -600.0)
        self.magn_z_min_ = self.get_parameter('magn_z_min').value

        self.declare_parameter("magn_z_max", 600.0)
        self.magn_z_max_ = self.get_parameter('magn_z_max').value

        self.declare_parameter("calibration_magn_use_extended", False)
        self.calibration_magn_use_extended_ = self.get_parameter('calibration_magn_use_extended').value
        
        self.declare_parameter("magn_ellipsoid_center", [0.0, 0.0, 0.0])
        self.magn_ellipsoid_center_ = self.get_parameter('magn_ellipsoid_center').value

        self.declare_parameter("magn_ellipsoid_transform",
            [0.0, 0.0, 0.0,
            0.0, 0.0, 0.0,
            0.0, 0.0, 0.0]
        )
        magn_ellipsoid_transform_1d = self.get_parameter('magn_ellipsoid_transform').value
        self.magn_ellipsoid_transform_ = np.zeros((len(self.magn_ellipsoid_center_), len(self.magn_ellipsoid_center_)))
        for i in range(len(self.magn_ellipsoid_center_)):
            for j in range(len(self.magn_ellipsoid_center_)):
                self.magn_ellipsoid_transform_[i][j] = magn_ellipsoid_transform_1d[i + j]

        self.declare_parameter("gyro_average_offset_x", 0.0)
        self.gyro_average_offset_x_ = self.get_parameter('gyro_average_offset_x').value

        self.declare_parameter("gyro_average_offset_y", 0.0)
        self.gyro_average_offset_y_ = self.get_parameter('gyro_average_offset_y').value

        self.declare_parameter("gyro_average_offset_z", 0.0)
        self.gyro_average_offset_z_ = self.get_parameter('gyro_average_offset_z').value

        self.get_logger().info(f"Opening {self.port_}")
        
        self.declare_parameter("baudrate", 57600)

        self.imuMsg = Imu()
        self.imuMsg.orientation_covariance = self.orientation_covariance_
        self.imuMsg.angular_velocity_covariance = self.angular_velocity_covariance_
        self.imuMsg.linear_acceleration_covariance = self.linear_acceleration_covariance_
        
        self.diag_pub_time = self.get_clock().now()

        try:
            self.ser_ = serial.Serial(port=self.port_, baudrate=self.get_parameter('baudrate').value, timeout=1)
            #ser = serial.Serial(port=port, baudrate=self.get_parameter('baudrate').value, timeout=1, rtscts=True, dsrdtr=True) # For compatibility with some virtual serial ports (e.g. created by socat) in Python 2.7
        except serial.serialutil.SerialException:
            self.get_logger().error(f"IMU not found at port {self.port_}. Did you specify the correct port in the launch file?")
            sys.exit(2)
        
        roll=0
        pitch=0
        yaw=0
        self.seq=0
        accel_factor = 9.806 / 256.0 # sensor reports accel as 256.0 = 1G (9.8m/s^2). Convert to m/s^2.

        self.get_logger().info("Giving the razor IMU board 5 seconds to boot...")
        time.sleep(5)

        ### configure board ###
        #stop datastream
        self.ser_.write(('#o0').encode("utf-8"))

        #discard old input
        #flush manually, as above command is not working
        discard = self.ser_.readlines() 
        
        #set output mode
        self.ser_.write(('#ox').encode("utf-8")) # To start display angle and sensor reading in text

        self.get_logger().info("Writing calibration values to razor IMU board...")

        self.ser_.write(('#caxm' + str(self.accel_x_min_)).encode("utf-8"))
        self.ser_.write(('#caxM' + str(self.accel_x_max_)).encode("utf-8"))
        self.ser_.write(('#caym' + str(self.accel_y_min_)).encode("utf-8"))
        self.ser_.write(('#cayM' + str(self.accel_y_max_)).encode("utf-8"))
        self.ser_.write(('#cazm' + str(self.accel_z_min_)).encode("utf-8"))
        self.ser_.write(('#cazM' + str(self.accel_z_max_)).encode("utf-8"))

        if not self.calibration_magn_use_extended_:
            self.ser_.write(('#cmxm' + str(self.magn_x_min_)).encode("utf-8"))
            self.ser_.write(('#cmxM' + str(self.magn_x_max_)).encode("utf-8"))
            self.ser_.write(('#cmym' + str(self.magn_y_min_)).encode("utf-8"))
            self.ser_.write(('#cmyM' + str(self.magn_y_max_)).encode("utf-8"))
            self.ser_.write(('#cmzm' + str(self.magn_z_min_)).encode("utf-8"))
            self.ser_.write(('#cmzM' + str(self.magn_z_max_)).encode("utf-8"))
        else:
            self.ser_.write(('#ccx' + str(self.magn_ellipsoid_center_[0])).encode("utf-8"))
            self.ser_.write(('#ccy' + str(self.magn_ellipsoid_center_[1])).encode("utf-8"))
            self.ser_.write(('#ccz' + str(self.magn_ellipsoid_center_[2])).encode("utf-8"))
            self.ser_.write(('#ctxX' + str(self.magn_ellipsoid_transform_[0][0])).encode("utf-8"))
            self.ser_.write(('#ctxY' + str(self.magn_ellipsoid_transform_[0][1])).encode("utf-8"))
            self.ser_.write(('#ctxZ' + str(self.magn_ellipsoid_transform_[0][2])).encode("utf-8"))
            self.ser_.write(('#ctyX' + str(self.magn_ellipsoid_transform_[1][0])).encode("utf-8"))
            self.ser_.write(('#ctyY' + str(self.magn_ellipsoid_transform_[1][1])).encode("utf-8"))
            self.ser_.write(('#ctyZ' + str(self.magn_ellipsoid_transform_[1][2])).encode("utf-8"))
            self.ser_.write(('#ctzX' + str(self.magn_ellipsoid_transform_[2][0])).encode("utf-8"))
            self.ser_.write(('#ctzY' + str(self.magn_ellipsoid_transform_[2][1])).encode("utf-8"))
            self.ser_.write(('#ctzZ' + str(self.magn_ellipsoid_transform_[2][2])).encode("utf-8"))
        
        self.ser_.write(('#cgx' + str(self.gyro_average_offset_x_)).encode("utf-8"))
        self.ser_.write(('#cgy' + str(self.gyro_average_offset_y_)).encode("utf-8"))
        self.ser_.write(('#cgz' + str(self.gyro_average_offset_z_)).encode("utf-8"))

        #print calibration values for verification by user
        self.ser_.flushInput()
        self.ser_.write(('#p').encode("utf-8"))
        calib_data = self.ser_.readlines()
        calib_data_print = "Printing set calibration values:\r\n"
        for row in calib_data:
            line = bytearray(row).decode("utf-8")
            calib_data_print += line
        self.get_logger().info(calib_data_print)

        #start datastream
        self.ser_.write(('#o1').encode("utf-8"))

        #automatic flush - NOT WORKING
        #ser.flushInput()  #discard old input, still in invalid format
        #flush manually, as above command is not working - it breaks the serial connection
        self.get_logger().info("Flushing first 200 IMU entries...")
        for _ in range(200):
            line = bytearray(self.ser_.readline()).decode("utf-8")
        self.get_logger().info("Publishing IMU data...")

        errcount = 0
        while rclpy.ok():
            if (errcount > 10):
                break
            line = bytearray(self.ser_.readline()).decode("utf-8")
            if ((line.find("#YPRAG=") == -1) or (line.find("\r\n") == -1)):
                self.get_logger().warn("Bad IMU data or bad sync")
                errcount = errcount+1
                continue
            line = line.replace("#YPRAG=","")   # Delete "#YPRAG="
            #f.write(line)                     # Write to the output log file
            line = line.replace("\r\n","")   # Delete "\r\n"
            words = line.split(",")    # Fields split
            if len(words) != 9:
                self.get_logger().warn("Bad IMU data or bad sync")
                errcount = errcount+1
                continue
            else:
                errcount = 0
                #in AHRS firmware z axis points down, in ROS z axis points up (see REP 103)
                yaw_deg = -float(words[0])
                yaw_deg = yaw_deg + self.imu_yaw_calib_
                if yaw_deg > 180.0:
                    yaw_deg = yaw_deg - 360.0
                if yaw_deg < -180.0:
                    yaw_deg = yaw_deg + 360.0
                yaw = yaw_deg*DEGREES_2_RAD
                #in AHRS firmware y axis points right, in ROS y axis points left (see REP 103)
                pitch = -float(words[1])*DEGREES_2_RAD
                roll = float(words[2])*DEGREES_2_RAD

                # Publish message
                # AHRS firmware accelerations are negated
                # This means y and z are correct for ROS, but x needs reversing
                self.imuMsg.linear_acceleration.x = -float(words[3]) * accel_factor
                self.imuMsg.linear_acceleration.y = float(words[4]) * accel_factor
                self.imuMsg.linear_acceleration.z = float(words[5]) * accel_factor

                self.imuMsg.angular_velocity.x = float(words[6])
                #in AHRS firmware y axis points right, in ROS y axis points left (see REP 103)
                self.imuMsg.angular_velocity.y = -float(words[7])
                #in AHRS firmware z axis points down, in ROS z axis points up (see REP 103) 
                self.imuMsg.angular_velocity.z = -float(words[8])

            q = quaternion_from_euler(roll,pitch,yaw)
            self.imuMsg.orientation.x = q[0]
            self.imuMsg.orientation.y = q[1]
            self.imuMsg.orientation.z = q[2]
            self.imuMsg.orientation.w = q[3]
            self.imuMsg.header.stamp= self.get_clock().now().to_msg()
            self.imuMsg.header.frame_id = self.frame_id_
            self.seq = self.seq + 1
            self.imu_pub_.publish(self.imuMsg)

            if (self.diag_pub_time < self.get_clock().now()) :
                diag_arr = DiagnosticArray()
                diag_arr.header.stamp = self.get_clock().now().to_msg()
                diag_arr.header.frame_id = '1'
                diag_msg = DiagnosticStatus()
                diag_msg.name = 'Razor_Imu'
                diag_msg.level = DiagnosticStatus.OK
                diag_msg.message = 'Received AHRS measurement'
                roll_key_val = KeyValue()
                yaw_key_val = KeyValue()
                pitch_key_val = KeyValue()
                seq_key_val = KeyValue()
                roll_key_val.key = 'roll (deg)'
                roll_key_val.value = str(roll * (180.0 / math.pi))
                yaw_key_val.key = 'yaw (deg)'
                yaw_key_val.value = str(yaw * (180.0 / math.pi))
                pitch_key_val.key = 'pitch (deg)'
                pitch_key_val.value = str(pitch * (180.0 / math.pi))

                seq_key_val.key= 'sequence number'
                seq_key_val.value = str(self.seq)

                diag_msg.values.append(roll_key_val)
                diag_msg.values.append(yaw_key_val)
                diag_msg.values.append(pitch_key_val)
                diag_msg.values.append(seq_key_val)
                diag_arr.status.append(diag_msg)
                self.diag_pub_.publish(diag_arr)
                
        self.ser_.close

        if (errcount > 10):
            sys.exit(10)



    def parameter_callback(self, params):
        success = False
        for param in params:
            if param.name == 'imu_yaw_calibration':
                if param.type == rclpy.Parameter.Type.DOUBLE:
                    if param.value >= MIN_YAW_CALIBRATION and param.value <= MAX_YAW_CALIBRATION:
                        self.get_logger().info(f"Reconfigure request for yaw calibration: {param.value}")
                        success = True
                        self.imu_yaw_calib_ = param.value
                        self.get_logger().info(f"Set imu yaw calibration to {self.imu_yaw_calib_}")
        return SetParametersResult(result=success)

def main(args = None):
    rclpy.init()
    node = RazorImuNode()
    rclpy.spin(RazorImuNode)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
