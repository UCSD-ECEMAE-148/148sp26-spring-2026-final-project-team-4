import os
from glob import glob
from setuptools import setup

package_name = 'razor_imu_9dof'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'param'), glob('param/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Siddharth Saha',
    maintainer_email='omadityasiddharth123@gmail.com',
    description='razor_imu_9dof is a package that provides a ROS2 driver for the Sparkfun OpenLog Artemis, 9DoF Razor IMU M0, 9DOF Razor IMU and 9DOF Sensor Stick. It also provides Arduino firmware that runs on the board, and which must be installed on it for the system to work. A node which displays the attitude (roll, pitch and yaw) of the board (or any IMU) is provided for testing.',
    license='BSD, GPLv3',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'imu_node = razor_imu_9dof.imu_node:main'
        ],
    },
)
