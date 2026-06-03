import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose
from std_msgs.msg import Bool, String
from tf2_ros import Buffer, TransformException, TransformListener


class MissionReturnNode(Node):
    def __init__(self):
        super().__init__('mission_return_node')
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('capture_timeout_s', 5.0)

        self.map_frame = str(self.get_parameter('map_frame').value)
        self.odom_frame = str(self.get_parameter('odom_frame').value)
        self.base_frame = str(self.get_parameter('base_frame').value)
        self.capture_timeout_s = float(self.get_parameter('capture_timeout_s').value)

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
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.start_pose = None
        self.capture_start_pose = False
        self.capture_requested_time = None
        self.return_in_progress = False
        self.capture_timer = self.create_timer(0.2, self.capture_timer_cb)

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
            self.capture_requested_time = self.get_clock().now()
            self.return_in_progress = False
            self.get_logger().info('Mission started; capturing start pose (AMCL or TF fallback)')

    def capture_timer_cb(self):
        if not self.capture_start_pose or self.start_pose is not None:
            return

        if self.capture_requested_time is not None:
            elapsed = (self.get_clock().now() - self.capture_requested_time).nanoseconds / 1e9
            if elapsed > self.capture_timeout_s:
                self.capture_start_pose = False
                self.get_logger().warning('Timed out capturing start pose from AMCL/TF')
                return

        self._try_capture_from_tf(self.map_frame)
        if self.start_pose is not None:
            return

        # Fallback for Stage 1 when map frame is still unstable; less accurate due to drift.
        self._try_capture_from_tf(self.odom_frame, warn=True)

    def start_pose_cb(self, msg: PoseWithCovarianceStamped):
        if not self.capture_start_pose:
            return

        self.start_pose = PoseStamped()
        self.start_pose.header = msg.header
        self.start_pose.pose = msg.pose.pose
        self.capture_start_pose = False
        self.capture_requested_time = None
        self.get_logger().info('Captured mission start pose from /amcl_pose')

    def _try_capture_from_tf(self, frame_id: str, warn: bool = False):
        try:
            tf = self.tf_buffer.lookup_transform(frame_id, self.base_frame, rclpy.time.Time())
        except TransformException:
            return

        pose = PoseStamped()
        pose.header.frame_id = frame_id
        pose.header.stamp = tf.header.stamp
        pose.pose.position.x = tf.transform.translation.x
        pose.pose.position.y = tf.transform.translation.y
        pose.pose.position.z = tf.transform.translation.z
        pose.pose.orientation = tf.transform.rotation

        self.start_pose = pose
        self.capture_start_pose = False
        self.capture_requested_time = None
        if warn:
            self.get_logger().warning(f'Captured mission start pose from TF {frame_id}->{self.base_frame} (fallback)')
        else:
            self.get_logger().info(f'Captured mission start pose from TF {frame_id}->{self.base_frame}')

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