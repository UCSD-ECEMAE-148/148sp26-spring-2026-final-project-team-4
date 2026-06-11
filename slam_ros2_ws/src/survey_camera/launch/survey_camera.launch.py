from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='survey_camera',
            executable='camera_node',
            name='survey_camera_node',
            output='screen',
        ),
        Node(
            package='survey_camera',
            executable='web_bridge',
            name='camera_web_bridge',
            output='screen',
        ),
    ])
