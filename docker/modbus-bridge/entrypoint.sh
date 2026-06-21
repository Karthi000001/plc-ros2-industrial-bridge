#!/bin/bash
# entrypoint.sh
# Activates ROS 2 environment variables before running any command.
# Without this, ros2 commands fail because the system cannot find ROS 2.
set -e

# Activate base ROS 2 Humble installation
source /opt/ros/humble/setup.bash

# Activate our built workspace (makes industrial_cell package findable)
source /ros2_ws/install/setup.bash

# Run whatever command was passed to docker run / CMD
exec "$@"
