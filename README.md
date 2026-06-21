# PLC–ROS 2 Industrial Cell Bridge

[![CI](https://github.com/YOUR_USERNAME/plc-ros2-industrial-bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/plc-ros2-industrial-bridge/actions)
![ROS 2 Humble](https://img.shields.io/badge/ROS2-Humble-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![PLC](https://img.shields.io/badge/IEC_61131--3-Structured_Text-orange)
![Python](https://img.shields.io/badge/Python-3.10-green)

Full OT-IT integration stack: IEC 61131-3 PLC → Modbus TCP → ROS 2 → AI Supervisor → Flask Dashboard.

## What it does

A real IEC 61131-3 Structured Text program runs inside OpenPLC, controlling a simulated
conveyor cell (belt + photoelectric sensor + gripper + fault latch). A Python ROS 2 node
reads the PLC state every 100ms via Modbus TCP and publishes it to ROS 2 topics. An AI
supervisor node (IsolationForest) trains on the first 200 normal cycles, then detects
anomalies and sends E-stop commands back to the PLC. A Flask dashboard shows live status.

## Architecture

```
OpenPLC (Modbus TCP :502)
  └─ conveyor_cell.st  ←──────────────────────────────┐
       belt_running   Coil 0 ──►                       │
       part_detected  Coil 1 ──►  modbus_bridge.py     │  /plc_commands
       gripper_active Coil 2 ──►  (ROS 2 node)         │◄── cell_supervisor.py
       fault_latch    Coil 3 ──►       │                │    (IsolationForest)
       cycle_count    Reg  0 ──►  /cell_state           │
       sensor_analog  Reg  1 ──►       │                │
                                       ▼            /supervisor_status
                               Flask Dashboard             │
                               http://localhost:5000 ◄─────┘
```

## Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/plc-ros2-industrial-bridge.git
cd plc-ros2-industrial-bridge

# 2. Start all containers
docker compose up --build

# 3. Load PLC program (once)
#    Open http://localhost:8080  (admin / admin)
#    Programs → New → paste plc/conveyor_cell.st → Compile → Upload → Go Online

# 4. Open dashboard
#    http://localhost:5000

# 5. Stop
docker compose down
```

## Folder Structure

```
plc-ros2-industrial-bridge/
├── .github/workflows/ci.yml          GitHub Actions CI
├── .vscode/                           VS Code settings, tasks, debugger
│   ├── settings.json
│   ├── extensions.json                Recommended extensions
│   ├── tasks.json                     Ctrl+Shift+B → run docker compose, git, etc.
│   └── launch.json                    F5 → debug Python nodes
├── plc/
│   └── conveyor_cell.st               IEC 61131-3 Structured Text PLC program
├── ros2_ws/src/industrial_cell/
│   ├── industrial_cell/
│   │   ├── modbus_bridge.py           Modbus TCP ↔ ROS 2 bridge node
│   │   └── cell_supervisor.py         IsolationForest anomaly detection node
│   └── launch/industrial_cell.launch.py
├── dashboard/
│   ├── app.py                         Flask REST API
│   └── templates/index.html           Live status web page
├── docker/                            Dockerfiles for each service
├── docs/                              ICD, FMEA, safety analysis
├── tests/                             Unit tests
└── docker-compose.yml                 4-service orchestration
```

## Skills Demonstrated

| Skill | Evidence |
|-------|----------|
| PLC / IEC 61131-3 | Real ST program: belt, sensor, gripper, TON timer, fault latch, watchdog |
| Industrial Automation | Complete pick-and-place cell architecture |
| System Integration | 4-layer stack: PLC → Modbus → ROS 2 → Dashboard |
| ROS 2 | 2-node pub/sub graph with launch file |
| Python | Bridge, supervisor (sklearn), Flask |
| Machine Learning | Unsupervised IsolationForest anomaly detection |
| Docker | 4-service compose with health checks and dependencies |
| Systems Engineering | Modbus register map = ICD, FMEA, safety analysis |
| Git | Feature branches, semantic commits, CI/CD |

## VS Code Integration

Open this folder in VS Code: `code .`

- **Ctrl+Shift+B** (or Terminal → Run Task): Docker build, Git commit/push, open browser tabs
- **F5**: Debug any Python node with breakpoints
- **Extensions**: Accept the recommended extensions prompt on first open

## Author

Karthikeyan Raja — Mechatronics Engineer / Robotics Systems Engineer Candidate
