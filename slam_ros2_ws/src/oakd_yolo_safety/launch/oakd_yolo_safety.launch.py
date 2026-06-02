from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    enable = LaunchConfiguration('enable')
    blob_path = LaunchConfiguration('blob_path')
    stop_on_detection = LaunchConfiguration('stop_on_detection')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')
    hazard_topic = LaunchConfiguration('hazard_topic')
    detection_topic = LaunchConfiguration('detection_topic')

    return LaunchDescription([
        DeclareLaunchArgument(
            'enable',
            default_value='true',
            description='Enable the Oak-D YOLO safety node',
        ),
        DeclareLaunchArgument(
            'blob_path',
            default_value='',
            description='Path to a DepthAI YOLO blob file',
        ),
        DeclareLaunchArgument(
            'stop_on_detection',
            default_value='true',
            description='Publish zero Twist when a hazard is detected',
        ),
        DeclareLaunchArgument(
            'cmd_vel_topic',
            default_value='/cmd_vel',
            description='Velocity topic to publish stop commands to',
        ),
        DeclareLaunchArgument(
            'hazard_topic',
            default_value='/oakd/yolo/hazard',
            description='Boolean hazard topic',
        ),
        DeclareLaunchArgument(
            'detection_topic',
            default_value='/oakd/yolo/detections',
            description='Detection summary topic',
        ),
        Node(
            package='oakd_yolo_safety',
            executable='oakd_yolo_safety_node',
            name='oakd_yolo_safety_node',
            output='screen',
            parameters=[{
                'enable': enable,
                'blob_path': blob_path,
                'stop_on_detection': stop_on_detection,
                'cmd_vel_topic': cmd_vel_topic,
                'hazard_topic': hazard_topic,
                'detection_topic': detection_topic,
            }],
            condition=IfCondition(enable),
        ),
    ])
