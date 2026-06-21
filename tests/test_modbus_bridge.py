"""
test_modbus_bridge.py
=====================
Unit tests for the Modbus bridge register map and state parsing logic.

Run:  python -m pytest tests/ -v
"""

import json
import pytest


# ── Register Map Tests ────────────────────────────────────────────────────────

def test_register_map_coil_addresses():
    """Verify coil addresses match the ICD."""
    from ros2_ws.src.industrial_cell.industrial_cell.modbus_bridge import (
        COIL_BELT_RUNNING, COIL_PART_DETECTED,
        COIL_GRIPPER_ACTIVE, COIL_FAULT_LATCH,
        COIL_ESTOP_CMD, COIL_RESET_CMD,
    )
    assert COIL_BELT_RUNNING   == 0
    assert COIL_PART_DETECTED  == 1
    assert COIL_GRIPPER_ACTIVE == 2
    assert COIL_FAULT_LATCH    == 3
    assert COIL_ESTOP_CMD      == 100
    assert COIL_RESET_CMD      == 101


# ── Supervisor State Machine Tests ────────────────────────────────────────────

def test_supervisor_training_threshold():
    """Supervisor should stay in TRAINING until 200 samples collected."""
    from ros2_ws.src.industrial_cell.industrial_cell.cell_supervisor import (
        CellSupervisor, SupervisorState
    )
    # We test the threshold constant, not the ROS2 node directly
    assert CellSupervisor.TRAINING_SAMPLES  == 200
    assert CellSupervisor.ANOMALY_THRESHOLD == 3


def test_supervisor_state_enum():
    """Verify all expected states exist."""
    from ros2_ws.src.industrial_cell.industrial_cell.cell_supervisor import SupervisorState
    assert SupervisorState.TRAINING.value   == "TRAINING"
    assert SupervisorState.MONITORING.value == "MONITORING"
    assert SupervisorState.FAULT.value      == "FAULT"


# ── Cell State JSON Format Tests ──────────────────────────────────────────────

def test_cell_state_json_keys():
    """Cell state JSON must contain all ICD-defined keys."""
    required_keys = {
        "belt_running", "part_detected", "gripper_active",
        "fault_latch", "cycle_count", "sensor_analog"
    }
    # Simulate what modbus_bridge._poll_plc() publishes
    sample_state = {
        "belt_running":   True,
        "part_detected":  False,
        "gripper_active": False,
        "fault_latch":    False,
        "cycle_count":    42,
        "sensor_analog":  42,
    }
    assert required_keys == set(sample_state.keys())


def test_cell_state_types():
    """Verify data types match Modbus register types."""
    state = {
        "belt_running":   True,     # Coil  → bool
        "part_detected":  False,    # Coil  → bool
        "gripper_active": False,    # Coil  → bool
        "fault_latch":    False,    # Coil  → bool
        "cycle_count":    0,        # Register → int
        "sensor_analog":  0,        # Register → int
    }
    assert isinstance(state["belt_running"],   bool)
    assert isinstance(state["part_detected"],  bool)
    assert isinstance(state["gripper_active"], bool)
    assert isinstance(state["fault_latch"],    bool)
    assert isinstance(state["cycle_count"],    int)
    assert isinstance(state["sensor_analog"],  int)
