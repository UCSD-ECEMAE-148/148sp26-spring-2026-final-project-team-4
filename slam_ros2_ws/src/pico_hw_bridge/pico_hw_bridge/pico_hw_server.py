import time
import serial

import rclpy
from rclpy.node import Node

from std_srvs.srv import Trigger
from example_interfaces.srv import SetBool


class PicoHardwareServer(Node):
    def __init__(self):
        super().__init__('pico_hw_server')

        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 115200)

        port = self.get_parameter('port').value
        baudrate = self.get_parameter('baudrate').value

        self.ser = serial.Serial(port, baudrate, timeout=1.0)
        time.sleep(2.0)

        self.create_service(Trigger, 'pico/ping', self.ping_callback)
        self.create_service(Trigger, 'pico/led_success', self.led_success_callback)
        self.create_service(Trigger, 'pico/led_failure', self.led_failure_callback)
        self.create_service(Trigger, 'pico/led_unknown', self.led_unknown_callback)
        self.create_service(Trigger, 'pico/led_off', self.led_off_callback)
        self.create_service(Trigger, 'pico/camera_center', self.camera_center_callback)

        self.get_logger().info(f'Connected to Pico on {port}')

    def send_command(self, command):
        self.ser.reset_input_buffer()
        self.ser.write((command + '\n').encode())
        self.ser.flush()

        response = self.ser.readline().decode(errors='ignore').strip()
        return response

    def make_trigger_response(self, pico_command, response):
        pico_response = self.send_command(pico_command)
        response.success = pico_response.startswith('ACK') or pico_response == 'PONG'
        response.message = pico_response
        return response

    def ping_callback(self, request, response):
        return self.make_trigger_response('PING', response)

    def led_success_callback(self, request, response):
        return self.make_trigger_response('LED:SUCCESS', response)

    def led_failure_callback(self, request, response):
        return self.make_trigger_response('LED:FAILURE', response)

    def led_unknown_callback(self, request, response):
        return self.make_trigger_response('LED:UNKNOWN', response)

    def led_off_callback(self, request, response):
        return self.make_trigger_response('LED:OFF', response)

    def camera_center_callback(self, request, response):
        return self.make_trigger_response('C_SERVO:CENTER', response)


def main(args=None):
    rclpy.init(args=args)
    node = PicoHardwareServer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()