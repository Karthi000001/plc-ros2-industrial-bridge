"""
cell_supervisor.py
==================
AI supervisor node for the industrial cell.

PHASES:
  TRAINING   — collects first 200 sensor readings as normal baseline
  MONITORING — IsolationForest detects deviations from baseline
  FAULT      — anomaly threshold exceeded, E-stop sent to PLC

Subscribes : /cell_state        (std_msgs/String — JSON from modbus_bridge)
Publishes  : /plc_commands      (std_msgs/String — JSON commands to bridge)
             /supervisor_status (std_msgs/String — JSON status for dashboard)

USAGE:
  ros2 run industrial_cell cell_supervisor
"""

import json
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sklearn.ensemble import IsolationForest
from enum import Enum


class SupervisorState(Enum):
    TRAINING   = "TRAINING"    # Collecting baseline — no detection yet
    MONITORING = "MONITORING"  # Active anomaly detection
    FAULT      = "FAULT"       # E-stop sent, awaiting manual reset


class CellSupervisor(Node):
    """
    Unsupervised anomaly detection supervisor for the industrial cell.

    Why IsolationForest?
    - Unsupervised: no labelled fault data needed
    - Learns 'normal' behaviour from the first N cycles automatically
    - Anomaly score is continuous: allows trend monitoring before threshold
    - Standard algorithm for predictive maintenance in industry

    Anomaly threshold = 3 consecutive detections before E-stop.
    Debouncing prevents false alarms from single sensor outliers.
    """

    TRAINING_SAMPLES  = 200   # Cycles to collect before fitting model
    ANOMALY_THRESHOLD = 3     # Consecutive anomalies needed for E-stop

    def __init__(self):
        super().__init__("cell_supervisor")

        # ── Publishers / Subscribers ──────────────────────────────────────────
        self.sub = self.create_subscription(
            String, "/cell_state", self._on_cell_state, 10
        )
        self.cmd_pub    = self.create_publisher(String, "/plc_commands",      10)
        self.status_pub = self.create_publisher(String, "/supervisor_status", 10)

        # ── State ─────────────────────────────────────────────────────────────
        self.state            = SupervisorState.TRAINING
        self.training_buffer  = []        # Accumulates baseline features
        self.model            = None      # IsolationForest, set after training
        self.consec_anomalies = 0
        self.prev_cycles      = 0
        self.total_processed  = 0

        self.get_logger().info(
            f"CellSupervisor started | "
            f"Collecting {self.TRAINING_SAMPLES} baseline samples ..."
        )

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_cell_state(self, msg: String):
        state = json.loads(msg.data)
        self.total_processed += 1

        # Feature vector: two values per reading
        # [sensor_analog]  — the process variable (0-100)
        # [delta_cycles]   — how many cycles since last reading (cycle rate)
        delta = state["cycle_count"] - self.prev_cycles
        feats = [float(state["sensor_analog"]), float(delta)]
        self.prev_cycles = state["cycle_count"]

        if self.state == SupervisorState.TRAINING:
            self._collect(feats)
        elif self.state == SupervisorState.MONITORING:
            self._detect(feats, state)

        # Always publish status so dashboard stays current
        self._publish_status(state["fault_latch"])

    # ── Training Phase ────────────────────────────────────────────────────────

    def _collect(self, feats: list):
        """Accumulate baseline samples; train when enough collected."""
        self.training_buffer.append(feats)
        n = len(self.training_buffer)

        if n % 50 == 0:
            self.get_logger().info(
                f"Training data: {n}/{self.TRAINING_SAMPLES} samples"
            )

        if n >= self.TRAINING_SAMPLES:
            self._train()

    def _train(self):
        """Fit IsolationForest on accumulated baseline data."""
        self.get_logger().info(
            f"Fitting IsolationForest on {len(self.training_buffer)} samples ..."
        )
        X = np.array(self.training_buffer)

        # contamination=0.05: assume up to 5% of training data may be anomalous
        # n_estimators=100:   100 isolation trees (more = better accuracy)
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
        )
        self.model.fit(X)
        self.state = SupervisorState.MONITORING
        self.get_logger().info("IsolationForest trained. Anomaly detection ACTIVE.")

    # ── Monitoring Phase ──────────────────────────────────────────────────────

    def _detect(self, feats: list, cell_state: dict):
        """Run inference and escalate to FAULT if threshold exceeded."""
        X     = np.array(feats).reshape(1, -1)
        pred  = self.model.predict(X)[0]          # 1=normal, -1=anomaly
        score = float(self.model.decision_function(X)[0])

        if pred == -1:
            self.consec_anomalies += 1
            self.get_logger().warn(
                f"ANOMALY | score={score:.4f} | "
                f"Consecutive: {self.consec_anomalies}/{self.ANOMALY_THRESHOLD}"
            )
        else:
            if self.consec_anomalies > 0:
                self.consec_anomalies = max(0, self.consec_anomalies - 1)

        if self.consec_anomalies >= self.ANOMALY_THRESHOLD:
            self.get_logger().error(
                "THRESHOLD EXCEEDED — sending E-STOP to PLC"
            )
            self._send(e_stop=True)
            self.state = SupervisorState.FAULT

    # ── Commands ──────────────────────────────────────────────────────────────

    def _send(self, e_stop: bool = False, reset: bool = False):
        """Publish a command for the Modbus bridge to write to PLC coils."""
        cmd = {}
        if e_stop:
            cmd["e_stop"] = True
        if reset:
            cmd["reset"]  = True
            cmd["e_stop"] = False
        msg      = String()
        msg.data = json.dumps(cmd)
        self.cmd_pub.publish(msg)

    # ── Status ────────────────────────────────────────────────────────────────

    def _publish_status(self, cell_fault: bool):
        status = {
            "supervisor_state":  self.state.value,
            "training_progress": len(self.training_buffer),
            "training_target":   self.TRAINING_SAMPLES,
            "consec_anomalies":  self.consec_anomalies,
            "total_processed":   self.total_processed,
            "cell_fault":        cell_fault,
        }
        msg      = String()
        msg.data = json.dumps(status)
        self.status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = CellSupervisor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
