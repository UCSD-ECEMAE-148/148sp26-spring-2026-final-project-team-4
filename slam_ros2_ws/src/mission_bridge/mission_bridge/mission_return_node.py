import math

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose
from std_msgs.msg import Bool, String


class MissionReturnNode(Node):
    def __init__(self):
        super().__init__('mission_return_node')
        self.start_pose_sub = self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl_pose',
            self.start_pose_cb,
            10,
        )
        self.command_sub = self.create_subscription(String, '/mission/control', self.command_cb, 10)
        self.started_sub = self.create_subscription(Bool, '/mission/started', self.started_cb, 10)
        self.complete_pub = self.create_publisher(Bool, '/mission/complete', 10)
        self.state_pub = self.create_publisher(String, '/mission/state', 10)
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.start_pose = None
        self.capture_start_pose = False
        self.return_in_progress = False

    def _publish_state(self, state: str):
        msg = String()
        msg.data = state
        self.state_pub.publish(msg)

    def _publish_complete(self):
        msg = Bool()
        msg.data = True
        self.complete_pub.publish(msg)

    def started_cb(self, msg: Bool):
        if msg.data:
            self.start_pose = None
            self.capture_start_pose = True
            self.return_in_progress = False

    def start_pose_cb(self, msg: PoseWithCovarianceStamped):
        if not self.capture_start_pose:
            return

        self.start_pose = PoseStamped()
        self.start_pose.header = msg.header
        self.start_pose.pose = msg.pose.pose
        self.capture_start_pose = False
        self.get_logger().info('Captured mission start pose from /amcl_pose')

    def command_cb(self, msg: String):
        if msg.data.strip().lower() != 'end':
            return
        if self.return_in_progress:
            self.get_logger().info('Return-to-start already in progress')
            return
        if self.start_pose is None:
            self.get_logger().warning('No start pose recorded yet; marking mission complete without return goal')
            self._publish_state('return_failed_no_start_pose')
            self._publish_complete()
            return

        self.return_in_progress = True
        self._publish_state('returning')
        self.get_logger().info('Sending return-to-start goal')
        if not self.nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('navigate_to_pose action server is unavailable')
            self.return_in_progress = False
            self._publish_state('return_failed_no_server')
            self._publish_complete()
            return

        goal = NavigateToPose.Goal()
        goal.pose = self._pose_to_goal(self.start_pose)
        future = self.nav_client.send_goal_async(goal)
        future.add_done_callback(self._goal_response_cb)

    def _pose_to_goal(self, pose_stamped: PoseStamped) -> PoseStamped:
        goal = PoseStamped()
        goal.header.frame_id = pose_stamped.header.frame_id or 'map'
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.pose.position.x = pose_stamped.pose.position.x
        goal.pose.position.y = pose_stamped.pose.position.y
        goal.pose.position.z = pose_stamped.pose.position.z
        goal.pose.orientation = pose_stamped.pose.orientation
        return goal

    def _goal_response_cb(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Return-to-start goal was rejected')
            self.return_in_progress = False
            self._publish_state('return_failed_rejected')
            self._publish_complete()
            return

        self.get_logger().info('Return-to-start goal accepted')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_cb)

    def _result_cb(self, future):
        result = future.result().result
        status = future.result().status
        self.return_in_progress = False
        if status == 4:
            self._publish_state('returned')
            self.get_logger().info('Robot returned to start position')
        else:
            self._publish_state(f'return_finished_status_{status}')
            self.get_logger().warning(f'Return goal finished with status {status}')
        self._publish_complete()


def main(args=None):
    rclpy.init(args=args)
    node = MissionReturnNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()