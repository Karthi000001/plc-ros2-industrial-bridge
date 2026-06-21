(* ========================================================================
   FILE:    conveyor_cell.st
   PROJECT: PLC-ROS2 Industrial Cell Bridge
   AUTHOR:  Karthikeyan Raja

   HOW TO LOAD INTO OPENPLC:
     1. Run:  docker compose up --build
     2. Open: http://localhost:8080   (Login: admin / admin)
     3. Click: Programs → New Program
     4. Name: conveyor_cell  |  Type: Structured Text (ST)
     5. Paste this entire file into the editor
     6. Click: Compile → Upload → Go Online

   MODBUS ADDRESS MAP  (this IS the Interface Control Document):
     Coil   0  : belt_running    READ  — belt motor relay
     Coil   1  : part_detected   READ  — photoelectric sensor
     Coil   2  : gripper_active  READ  — gripper solenoid
     Coil   3  : fault_latch     READ  — latched system fault
     Coil 100  : e_stop_cmd      WRITE — E-stop from ROS2 supervisor
     Coil 101  : reset_cmd       WRITE — reset from ROS2 supervisor
     Register 0: cycle_count     READ  — completed cycle counter
     Register 1: sensor_analog   READ  — simulated analog value 0-100
   ======================================================================== *)

PROGRAM conveyor_cell
VAR
    (* ── INPUTS mapped to Modbus Coils via OpenPLC address table ─── *)
    part_detected   : BOOL;    (* Coil   1 : photoelectric sensor signal *)
    e_stop_cmd      : BOOL;    (* Coil 100 : E-stop command from ROS2    *)
    reset_cmd       : BOOL;    (* Coil 101 : reset command from ROS2     *)

    (* ── OUTPUTS written by this program, readable via Modbus ─────── *)
    belt_running    : BOOL;    (* Coil   0 : belt motor relay            *)
    gripper_active  : BOOL;    (* Coil   2 : gripper solenoid valve      *)
    fault_latch     : BOOL;    (* Coil   3 : latched fault flag          *)

    (* ── INTERNAL: timers and counters ───────────────────────────── *)
    (* TON = On-Delay Timer
       IN : starts timer when TRUE, resets when FALSE
       PT : preset time to wait
       Q  : output TRUE when IN has been TRUE for >= PT              *)
    gripper_timer   : TON;

    (* Watchdog: trip fault if no part detected for 30 seconds        *)
    watchdog_timer  : TON;

    (* Holding Registers: 16-bit integers readable by Modbus          *)
    cycle_count     : INT := 0;     (* Register 0 *)
    sensor_analog   : INT := 0;     (* Register 1 *)
END_VAR


(* ── PRIORITY 1: E-STOP (checked every scan, highest priority) ──── *)
(* If E-stop commanded: stop everything, latch fault, exit scan       *)
IF e_stop_cmd THEN
    fault_latch    := TRUE;
    belt_running   := FALSE;
    gripper_active := FALSE;
    gripper_timer(IN := FALSE, PT := T#500ms);
    RETURN;
END_IF;

(* ── PRIORITY 2: FAULT RESET ─────────────────────────────────────── *)
(* Both reset_cmd AND NOT e_stop must be true to clear fault          *)
IF reset_cmd AND NOT e_stop_cmd THEN
    fault_latch := FALSE;
    reset_cmd   := FALSE;
END_IF;

(* Keep actuators stopped while any fault is active                   *)
IF fault_latch THEN
    belt_running   := FALSE;
    gripper_active := FALSE;
    RETURN;
END_IF;

(* ── PRIORITY 3: NORMAL OPERATION ───────────────────────────────── *)

belt_running := TRUE;

(* Gripper control via 500ms TON timer:
   - part_detected TRUE  → timer starts counting
   - 0..499ms            → gripper_active TRUE (clamping)
   - 500ms elapsed       → gripper_active FALSE (release)
   - part_detected FALSE → timer resets                              *)
IF part_detected AND NOT gripper_timer.Q THEN
    gripper_timer(IN := TRUE, PT := T#500ms);
ELSE
    IF NOT part_detected THEN
        gripper_timer(IN := FALSE, PT := T#500ms);
    END_IF;
END_IF;

gripper_active := gripper_timer.IN AND NOT gripper_timer.Q;

(* Increment cycle counter when gripper completes hold               *)
IF gripper_timer.Q THEN
    cycle_count   := cycle_count + 1;
    sensor_analog := cycle_count MOD 100;
END_IF;

(* Watchdog: fault if no part detected for 30 consecutive seconds    *)
watchdog_timer(IN := NOT part_detected, PT := T#30s);
IF watchdog_timer.Q THEN
    fault_latch := TRUE;
END_IF;

END_PROGRAM


CONFIGURATION default_config
    RESOURCE res0 ON PLC
        TASK TaskMain(INTERVAL := T#100ms, PRIORITY := 0);
        PROGRAM Inst0 WITH TaskMain : conveyor_cell;
    END_RESOURCE
END_CONFIGURATION
