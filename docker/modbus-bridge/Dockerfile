# Base: official ROS 2 Humble (LTS — supported until 2027)
FROM ros:humble-ros-base-jammy

# Install Python package manager and ROS 2 build tool
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies for our ROS 2 nodes
RUN pip3 install --no-cache-dir \
    pymodbus \
    scikit-learn \
    numpy

# Copy and build the ROS 2 workspace
WORKDIR /ros2_ws
COPY ros2_ws/ .
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build --symlink-install"

# Entrypoint: activates ROS 2 environment before any command runs
COPY docker/modbus-bridge/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# Default command: launch both ROS 2 nodes
CMD ["ros2", "launch", "industrial_cell", "industrial_cell.launch.py"]
