# FMEA — PLC-ROS2 Industrial Cell Bridge

**System:** PLC-ROS2 Industrial Cell Bridge
**Version:** 1.0
**Author:** Karthikeyan Raja

## Severity / Occurrence / Detection Scale

| Rating | 1 | 2-3 | 4-6 | 7-8 | 9-10 |
|--------|---|-----|-----|-----|------|
| Severity | No effect | Minor | Moderate | High | Catastrophic |
| Occurrence | Very unlikely | Unlikely | Moderate | Likely | Very likely |
| Detection | Certain | High | Moderate | Low | Undetectable |

**RPN = Severity × Occurrence × Detection** (lower is better, target < 100)

---

## Failure Mode Table

| ID | Component | Failure Mode | Effect on System | S | O | D | RPN | Mitigation |
|----|-----------|-------------|-----------------|---|---|---|-----|------------|
| F01 | OpenPLC container | PLC crash / container stop | All outputs de-energise | 7 | 2 | 1 | 14 | Fail-safe: actuators default OFF on power loss. Docker restart: unless-stopped |
| F02 | Modbus TCP connection | Bridge loses PLC connection | /cell_state stops publishing | 8 | 3 | 2 | 48 | Connection retry logic (15 attempts, exp backoff). Log error to ROS2 |
| F03 | IsolationForest | False positive anomaly | Unnecessary E-stop, production stop | 5 | 3 | 3 | 45 | Debounce: 3 consecutive detections needed. Contamination=0.05 |
| F04 | IsolationForest | False negative (missed anomaly) | Cell runs in degraded state | 8 | 2 | 5 | 80 | Future: add supervised model as second layer after fault data collected |
| F05 | E-stop write | Modbus write coil fails | PLC does not receive E-stop | 9 | 2 | 3 | 54 | Verify coil on next read; log persistent failure; CI test covers write path |
| F06 | PLC watchdog timer | Logic error in ST program | No fault trip on jammed belt | 7 | 1 | 2 | 14 | Code reviewed. Watchdog tested by simulating 30s no-part condition |
| F07 | Docker networking | Service DNS fails | ros2-bridge cannot reach openplc | 7 | 2 | 2 | 28 | Docker internal DNS is reliable; healthcheck + depends_on ordering |
| F08 | Flask dashboard | Web server crash | No visibility (operators blind) | 4 | 2 | 1 | 8 | Dashboard is monitoring only — no control. Safety functions independent |

---

## Highest Risk Item: F05 (RPN 54)

**Root cause:** Modbus write_coil() can silently fail if TCP connection drops
mid-transaction.

**Current mitigation:** Read coil 100 on next poll cycle; if E-stop was commanded
but coil reads FALSE, log critical error and retry.

**Future action:** Implement write-verify pattern in modbus_bridge._on_command().
