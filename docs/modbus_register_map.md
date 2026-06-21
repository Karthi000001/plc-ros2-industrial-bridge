# Interface Control Document (ICD)
# Modbus Register Map — PLC ↔ ROS 2 Interface

**System:** PLC-ROS2 Industrial Cell Bridge
**Version:** 1.0
**Author:** Karthikeyan Raja
**Interface:** OpenPLC Modbus TCP server (port 502)

---

## Purpose

Defines every data variable exchanged between the PLC layer (OpenPLC)
and the ROS 2 layer (modbus_bridge.py) via Modbus TCP protocol.

This document must be reviewed and agreed upon by:
- PLC programmer (owns the ST program)
- ROS 2 developer (owns modbus_bridge.py)

Any change to this document requires updating BOTH the ST program
AND the modbus_bridge.py constants before testing.

---

## Coil Table (1-bit Boolean values)

| Modbus Address | Variable Name   | Direction     | Data Type | Description                                     |
|---------------|-----------------|---------------|-----------|-------------------------------------------------|
| 0             | belt_running    | PLC → ROS2    | BOOL      | Belt motor relay: TRUE=running, FALSE=stopped   |
| 1             | part_detected   | PLC → ROS2    | BOOL      | Photoelectric sensor: TRUE=part in gripper zone |
| 2             | gripper_active  | PLC → ROS2    | BOOL      | Gripper solenoid: TRUE=clamped, FALSE=open      |
| 3             | fault_latch     | PLC → ROS2    | BOOL      | Latched fault flag: TRUE=fault active           |
| 100           | e_stop_cmd      | ROS2 → PLC    | BOOL      | Emergency stop command: TRUE=stop all actuators |
| 101           | reset_cmd       | ROS2 → PLC    | BOOL      | Fault reset: TRUE=clear fault_latch (self-clears)|

## Holding Register Table (16-bit Integer values)

| Modbus Address | Variable Name   | Direction     | Data Type | Range   | Description                         |
|---------------|-----------------|---------------|-----------|---------|-------------------------------------|
| 0             | cycle_count     | PLC → ROS2    | INT16     | 0-32767 | Completed pick-and-place cycle count|
| 1             | sensor_analog   | PLC → ROS2    | INT16     | 0-100   | Simulated analog process variable   |

---

## ROS 2 Topic Interface

| Topic              | Publisher      | Subscriber       | Type   | Rate   | Content                    |
|--------------------|----------------|------------------|--------|--------|----------------------------|
| /cell_state        | modbus_bridge  | cell_supervisor  | String | 10 Hz  | JSON with all coil+reg values|
| /plc_commands      | cell_supervisor| modbus_bridge    | String | on demand | JSON with e_stop/reset   |
| /supervisor_status | cell_supervisor| dashboard        | String | 10 Hz  | JSON with AI supervisor state|

---

## Interface Verification

Each coil verified by:
1. Loading conveyor_cell.st into OpenPLC → Go Online
2. Running: `docker compose logs -f ros2-bridge`
3. Checking /cell_state publishes correct values at 10 Hz
4. Writing test commands via: `ros2 topic pub /plc_commands std_msgs/String '{"data": "{\"e_stop\": true}"}'`
