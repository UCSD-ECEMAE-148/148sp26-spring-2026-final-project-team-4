import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('robot_slam')
    mission_bridge_pkg = get_package_share_directory('mission_bridge')

    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    use_rviz = LaunchConfiguration('use_rviz')
    enable_exploration = LaunchConfiguration('enable_exploration')
    exploration_auto_start = LaunchConfiguration('exploration_auto_start')
    exploration_publish_end_on_complete = LaunchConfiguration('exploration_publish_end_on_complete')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulated clock',
        ),
        DeclareLaunchArgument(
            'autostart',
            default_value='true',
            description='Automatically start the Nav2 lifecycle stack',
        ),
        DeclareLaunchArgument(
            'use_rviz',
            default_value='false',
            description='Launch RViz with the mapping layout',
        ),
        DeclareLaunchArgument(
            'enable_exploration',
            default_value='true',
            description='Launch the frontier exploration planner node',
        ),
        DeclareLaunchArgument(
            'exploration_auto_start',
            default_value='true',
            description='Start exploration immediately without mission start command',
        ),
        DeclareLaunchArgument(
            'exploration_publish_end_on_complete',
            default_value='false',
            description='Publish mission end command when exploration is complete',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg, 'launch', 'slam.launch.py')
            ),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'autostart': autostart,
                'use_rviz': use_rviz,
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(mission_bridge_pkg, 'launch', 'mission_bridge.launch.py')
            ),
        ),
        Node(
            package='frontier_explorer',
            executable='frontier_explorer_node',
            name='frontier_explorer_node',
            output='screen',
            parameters=[{
                'auto_start': exploration_auto_start,
                'publish_end_on_complete': exploration_publish_end_on_complete,
            }],
            condition=IfCondition(enable_exploration),
        ),
    ])
