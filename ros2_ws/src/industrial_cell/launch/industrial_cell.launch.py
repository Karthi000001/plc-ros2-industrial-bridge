"""
industrial_cell.launch.py
=========================
Launches both ROS 2 nodes for the industrial cell bridge.

USAGE:
  ros2 launch industrial_cell industrial_cell.launch.py
  ros2 launch industrial_cell industrial_cell.launch.py plc_host:=192.168.1.10
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([

        # ── Launch Arguments ──────────────────────────────────────────────────
        DeclareLaunchArgument(
            "plc_host",
            default_value="openplc",
            description="Hostname or IP of the OpenPLC Modbus TCP server",
        ),
        DeclareLaunchArgument(
            "plc_port",
            default_value="502",
            description="Modbus TCP port (default 502)",
        ),

        # ── Nodes ─────────────────────────────────────────────────────────────
        Node(
            package="industrial_cell",
            executable="modbus_bridge",
            name="modbus_bridge",
            parameters=[{
                "plc_host": LaunchConfiguration("plc_host"),
                "plc_port": LaunchConfiguration("plc_port"),
                "poll_hz":  10.0,
            }],
            output="screen",
        ),

        Node(
            package="industrial_cell",
            executable="cell_supervisor",
            name="cell_supervisor",
            output="screen",
        ),

    ])
