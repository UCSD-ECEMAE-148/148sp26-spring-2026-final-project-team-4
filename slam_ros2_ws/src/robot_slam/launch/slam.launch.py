from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg = get_package_share_directory('robot_slam')

    return LaunchDescription([

        # Robot description
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': open(
                os.path.join(pkg, 'urdf', 'robot.urdf.xacro')).read()}]
        ),

        # Local EKF — fuses IMU + visual odom
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_local_node',
            parameters=[os.path.join(pkg, 'config', 'ekf_local.yaml')],
            remappings=[('odometry/filtered', 'odometry/local')]
        ),

        # Global EKF — fuses local odom + GPS
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_global_node',
            parameters=[os.path.join(pkg, 'config', 'ekf_global.yaml')],
            remappings=[('odometry/filtered', 'odometry/global')]
        ),

        # GPS conversion
        Node(
            package='robot_localization',
            executable='navsat_transform_node',
            parameters=[os.path.join(pkg, 'config', 'ekf_global.yaml')],
            remappings=[
                ('imu/data', '/imu/data'),
                ('gps/fix', '/gps/fix'),
                ('odometry/filtered', 'odometry/local'),
            ]
        ),

        # SLAM Toolbox
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            parameters=[os.path.join(pkg, 'config', 'slam_toolbox.yaml')],
        ),
    ])