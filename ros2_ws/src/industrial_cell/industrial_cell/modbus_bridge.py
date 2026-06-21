"""
modbus_bridge.py
================
Bridges OpenPLC (Modbus TCP) to the ROS 2 topic layer.

DATA FLOW:
  PLC → Modbus TCP → this node → /cell_state  (publish, 10 Hz)
  /plc_commands → this node → Modbus TCP → PLC coils (write on demand)

MODBUS ADDRESS MAP  (Interface Control Document):
  Coil   0  belt_running    READ
  Coil   1  part_detected   READ
  Coil   2  gripper_active  READ
  Coil   3  fault_latch     READ
  Coil 100  e_stop_cmd      WRITE  (ROS2 → PLC)
  Coil 101  reset_cmd       WRITE  (ROS2 → PLC)
  Reg    0  cycle_count     READ
  Reg    1  sensor_analog   READ

USAGE:
  ros2 run industrial_cell modbus_bridge
  ros2 run industrial_cell modbus_bridge --ros-args -p plc_host:=192.168.1.10
"""

import json
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException


# ── Modbus Register Map ───────────────────────────────────────────────────────
# These constants ARE the ICD. Every address is documented.
# Change here = change the interface. Inform the PLC programmer.
COIL_BELT_RUNNING   = 0
COIL_PART_DETECTED  = 1
COIL_GRIPPER_ACTIVE = 2
COIL_FAULT_LATCH    = 3
COIL_ESTOP_CMD      = 100   # WRITE: E-stop command  (ROS2 → PLC)
COIL_RESET_CMD      = 101   # WRITE: Reset command   (ROS2 → PLC)
REG_CYCLE_COUNT     = 0
REG_SENSOR_ANALOG   = 1
# ─────────────────────────────────────────────────────────────────────────────


class ModbusBridge(Node):
    """
    ROS 2 node that polls OpenPLC via Modbus TCP and bridges to ROS 2 topics.

    Publishes  : /cell_state       (std_msgs/String — JSON)
    Subscribes : /plc_commands     (std_msgs/String — JSON)

    /cell_state JSON keys:
        belt_running   : bool
        part_detected  : bool
        gripper_active : bool
        fault_latch    : bool
        cycle_count    : int
        sensor_analog  : int

    /plc_commands JSON keys (any combination):
        e_stop : bool   → writes to COIL_ESTOP_CMD
        reset  : bool   → writes to COIL_RESET_CMD
    """

    def __init__(self):
        super().__init__("modbus_bridge")

        # ── ROS 2 Parameters (can be set from launch file or CLI) ─────────────
        self.declare_parameter("plc_host", "openplc")
        self.declare_parameter("plc_port", 502)
        self.declare_parameter("poll_hz",  10.0)

        host     = self.get_parameter("plc_host").get_parameter_value().string_value
        port     = self.get_parameter("plc_port").get_parameter_value().integer_value
        poll_hz  = self.get_parameter("poll_hz").get_parameter_value().double_value

        # ── Publishers / Subscribers ──────────────────────────────────────────
        self.pub = self.create_publisher(String, "/cell_state", 10)
        self.sub = self.create_subscription(
            String, "/plc_commands", self._on_command, 10
        )

        # ── Connect to PLC with retry ─────────────────────────────────────────
        self.client = self._connect_with_retry(host, port)

        # ── Polling timer ─────────────────────────────────────────────────────
        self.timer = self.create_timer(1.0 / poll_hz, self._poll_plc)
        self.get_logger().info(
            f"ModbusBridge running | PLC={host}:{port} | Poll={poll_hz} Hz"
        )

    # ── Private Methods ───────────────────────────────────────────────────────

    def _connect_with_retry(self, host: str, port: int,
                             max_retries: int = 15) -> ModbusTcpClient:
        """Connect to PLC with exponential back-off.

        OpenPLC may take 10-30 seconds to load the program after container
        start, so we retry patiently rather than failing immediately.
        """
        for attempt in range(1, max_retries + 1):
            self.get_logger().info(
                f"Connecting to PLC {host}:{port}  (attempt {attempt}/{max_retries})"
            )
            client = ModbusTcpClient(host, port=port, timeout=3)
            if client.connect():
                self.get_logger().info("Connected to PLC.")
                return client
            wait = min(2 * attempt, 10)
            self.get_logger().warn(f"Retrying in {wait}s ...")
            time.sleep(wait)
        self.get_logger().error("Could not connect to PLC. Exiting.")
        raise SystemExit(1)

    def _poll_plc(self):
        """Poll PLC every 100ms and publish current state to /cell_state."""
        try:
            coils = self.client.read_coils(0, 8)
            regs  = self.client.read_holding_registers(0, 2)

            if coils.isError() or regs.isError():
                self.get_logger().warn("Modbus read error — skipping cycle")
                return

            state = {
                "belt_running":   bool(coils.bits[COIL_BELT_RUNNING]),
                "part_detected":  bool(coils.bits[COIL_PART_DETECTED]),
                "gripper_active": bool(coils.bits[COIL_GRIPPER_ACTIVE]),
                "fault_latch":    bool(coils.bits[COIL_FAULT_LATCH]),
                "cycle_count":    int(regs.registers[REG_CYCLE_COUNT]),
                "sensor_analog":  int(regs.registers[REG_SENSOR_ANALOG]),
            }

            msg      = String()
            msg.data = json.dumps(state)
            self.pub.publish(msg)

        except ModbusException as exc:
            self.get_logger().error(f"Modbus error: {exc}")

    def _on_command(self, msg: String):
        """Write commands received from ROS 2 supervisor to PLC coils."""
        try:
            cmd = json.loads(msg.data)

            if "e_stop" in cmd:
                val = bool(cmd["e_stop"])
                self.client.write_coil(COIL_ESTOP_CMD, val)
                self.get_logger().warn(f"E-STOP → PLC: {val}")

            if "reset" in cmd:
                val = bool(cmd["reset"])
                self.client.write_coil(COIL_RESET_CMD, val)
                self.get_logger().info(f"RESET → PLC: {val}")

        except (json.JSONDecodeError, ModbusException) as exc:
            self.get_logger().error(f"Command write error: {exc}")

    def destroy_node(self):
        self.client.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ModbusBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
