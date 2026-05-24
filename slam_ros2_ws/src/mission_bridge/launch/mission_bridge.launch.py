import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()

    # Launch the three mission_bridge nodes
    ld.add_action(Node(
        package='mission_bridge',
        executable='image_capture_node',
        name='image_capture_node',
        output='screen',
    ))

    ld.add_action(Node(
        package='mission_bridge',
        executable='path_recorder_node',
        name='path_recorder_node',
        output='screen',
    ))

    ld.add_action(Node(
        package='mission_bridge',
        executable='mission_trigger_node',
        name='mission_trigger_node',
        output='screen',
    ))

    # Note: rosbridge_server / rosbridge_websocket_launch.xml is required
    # to accept WebSocket connections on ws://localhost:9090. If not installed,
    # add rosbridge_suite to system packages or apt. The user should install
    # rosbridge_server or start it separately. Optionally include it here if
    # available in the environment.

    return ld
