# Data Dictionary

| Entity | Field | Type | Req | Allowed Values / Format | Description |
|---|---|---|---|---|---|
| **Plant** | `plant_id` | String | Yes | `PLANT-001` to `PLANT-004` | Primary Key. |
| | `name` | String | Yes | Text | Operational plant facility name. |
| | `location` | String | Yes | Text | City / Region. |
| **Machine** | `machine_id` | String | Yes | `MCH-001` to `MCH-060` | Primary Key. |
| | `plant_id` | String | Yes | FK -> Plant.plant_id | Parent facility. |
| | `machine_type` | String | Yes | `CNC`, `Press`, `RoboticArm`, `Conveyor` | Category of industrial asset. |
| | `current_state` | String | Yes | `RUNNING`, `IDLE`, `TRIPPED`, `MAINTENANCE` | Machine operational state. |
| **SafetyZone** | `zone_id` | String | Yes | `SAFE-<plant_id>-001` | Primary Key. Safety enclosure. |
| | `plant_id` | String | Yes | FK -> Plant.plant_id | Parent facility. |
| | `risk_category`| String | Yes | `CAT1`, `CAT2`, `CAT3`, `CAT4` | ISO 13849-1 safety classification. |
| **Interlock** | `interlock_id` | String | Yes | `INT-<machine_id>-01` | Primary Key. |
| | `machine_id` | String | Yes | FK -> Machine.machine_id | Guarded equipment. |
| | `zone_id` | String | Yes | FK -> SafetyZone.zone_id | Physical zone boundary. |
| | `state` | String | Yes | `ENGAGED`, `DISENGAGED`, `FAULT` | Current physical sensor state. |
| **AlarmDef** | `alarm_def_id` | String | Yes | `DEF-001` to `DEF-200` | Primary Key. |
| | `severity` | String | Yes | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | ISA-18.2 Severity rating. |
| | `ack_sla_sec` | Int | Yes | `60` to `3600` | Allowed acknowledgment window in seconds. |
| **AlarmEvent** | `alarm_id` | String | Yes | `ALM-<machine_id>-000001` | Primary Key. |
| | `machine_id` | String | Yes | FK -> Machine.machine_id | Originating machine. |
| | `alarm_def_id`| String | Yes | FK -> AlarmDef.alarm_def_id | Definition template. |
| | `timestamp` | Datetime | Yes | ISO8601 | Detection timestamp. |
| | `is_flood` | Bool | Yes | `True`, `False` | Triggered during alarm flood condition. |
| **OperatorShift**| `shift_id` | String | Yes | `SFT-<plant_id>-0001` | Primary Key. |
| | `plant_id` | String | Yes | FK -> Plant.plant_id | Shift facility. |
| | `operator_id` | String | Yes | Text | Assigned worker. |
| | `start_time` | Datetime | Yes | ISO8601 | Shift start timestamp. |
| | `end_time` | Datetime | Yes | ISO8601 | Shift end timestamp. |
| **Ack** | `ack_id` | String | Yes | `ACK-<alarm-id>-01` | Primary Key. |
| | `alarm_id` | String | Yes | FK -> AlarmEvent.alarm_id | Parent alarm. |
| | `ack_time` | Datetime | Yes | ISO8601 | Time acknowledged. |
| | `operator_id` | String | Yes | Text | Operator completing acknowledgment. |
| **Incident** | `incident_id`| String | Yes | `INC-2026-000001` | Primary Key. |
| | `machine_id` | String | Yes | FK -> Machine.machine_id | Asset where event occurred. |
| | `zone_id` | String | Yes | FK -> SafetyZone.zone_id | Zone breached. |
| | `timestamp` | Datetime | Yes | ISO8601 | Incident occurrence time. |
| | `severity` | String | Yes | `MINOR`, `MAJOR`, `CRITICAL` | Incident level. |
| **Action** | `action_id` | String | Yes | `ACT-<incident-id>-01` | Primary Key. |
| | `incident_id` | String | Yes | FK -> Incident.incident_id | Target incident. |
| | `action_state`| String | Yes | `OPEN`, `RESOLVED`, `VERIFIED` | Lifecycle resolution status. |
| | `completion_time`| Datetime | No | ISO8601 | Sign-off timestamp. |
