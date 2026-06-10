import os

from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch import LaunchDescription

def generate_launch_description():

    param_dir = get_package_share_directory('razor_imu_9dof')

    params_declare = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(
            param_dir, 'param', 'razor.yaml'),
        description='File Path to Parameter File to use'
    )
    
    driver_node = Node(
        package='razor_imu_9dof',
        executable='imu_node',
        output='screen',
        parameters=[LaunchConfiguration('params_file')],
        remappings=[
            ('imu', '/razor/imu'),
            ('diagnostics', '/razor/diagnostics')
        ]
    )

    return LaunchDescription([
        params_declare,
        driver_node
    ])

