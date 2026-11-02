"""
Deterministic Synthetic Industrial Safety & Alarm Generator.
Follows deterministic ID nomenclature and strictly orders parent/child records.
"""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd


class SyntheticDataGenerator:

    def __init__(
        self,
        seed: int = 20261022,
        num_plants: int = 4,
        num_machines: int = 60,
        num_defs: int = 200,
        target_alarms: int = 50000,
        start_date: str = "2026-10-01 00:00:00",
        days: int = 30,
    ):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.num_plants = num_plants
        self.num_machines = num_machines
        self.num_defs = num_defs
        self.target_alarms = target_alarms
        self.start_dt = datetime.fromisoformat(start_date)
        self.end_dt = self.start_dt + timedelta(days=days)

    def generate_masters(self):
        # 1. Plants
        plants = [
            {
                "plant_id": f"PLANT-{i+1:03d}",
                "name": f"Factory Alpha-{chr(65+i)}",
                "location": loc,
            }
            for i, loc in enumerate(
                ["Detroit, MI", "Stuttgart, DE", "Pune, IN", "Nagoya, JP"][
                    : self.num_plants
                ]
            )
        ]
        df_plants = pd.DataFrame(plants)

        # 2. Safety Zones (3 zones per plant)
        zones = []
        for p in plants:
            p_id = p["plant_id"]
            for z_idx in range(1, 4):
                zones.append(
                    {
                        "zone_id": f"SAFE-{p_id}-{z_idx:03d}",
                        "plant_id": p_id,
                        "risk_category": self.rng.choice(
                            ["CAT1", "CAT2", "CAT3", "CAT4"],
                            p=[0.1, 0.3, 0.4, 0.2],
                        ),
                    }
                )
        df_zones = pd.DataFrame(zones)

        # 3. Machines distributed evenly across plants and assigned to zones
        machines = []
        m_types = ["CNC", "Press", "RoboticArm", "Conveyor"]
        for m_idx in range(1, self.num_machines + 1):
            m_id = f"MCH-{m_idx:03d}"
            p_id = f"PLANT-{(m_idx % self.num_plants) + 1:03d}"
            p_zones = [z["zone_id"] for z in zones if z["plant_id"] == p_id]
            assigned_zone = self.rng.choice(p_zones)
            machines.append(
                {
                    "machine_id": m_id,
                    "plant_id": p_id,
                    "zone_id": assigned_zone,
                    "machine_type": self.rng.choice(m_types),
                    "current_state": "RUNNING",
                }
            )
        df_machines = pd.DataFrame(machines)

        # 4. Interlocks (1-2 interlocks per machine)
        interlocks = []
        for m in machines:
            num_int = self.rng.integers(1, 3)
            for i in range(1, num_int + 1):
                interlocks.append(
                    {
                        "interlock_id": f"INT-{m['machine_id']}-{i:02d}",
                        "machine_id": m["machine_id"],
                        "zone_id": m["zone_id"],
                        "state": "ENGAGED",
                    }
                )
        df_interlocks = pd.DataFrame(interlocks)

        # 5. Alarm Definitions
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        sev_weights = [0.45, 0.35, 0.15, 0.05]
        slas = {"LOW": 3600, "MEDIUM": 1800, "HIGH": 300, "CRITICAL": 60}
        alarm_defs = []
        for d_idx in range(1, self.num_defs + 1):
            sev = self.rng.choice(severities, p=sev_weights)
            alarm_defs.append(
                {
                    "alarm_def_id": f"DEF-{d_idx:03d}",
                    "name": f"Sensor threshold breach code {d_idx}",
                    "severity": sev,
                    "ack_sla_sec": slas[sev],
                }
            )
        df_alarm_defs = pd.DataFrame(alarm_defs)

        return df_plants, df_zones, df_machines, df_interlocks, df_alarm_defs

    def generate_shifts(self, df_plants):
        shifts = []
        cur = self.start_dt
        shift_counter = 1
        while cur < self.end_dt:
            for p_id in df_plants["plant_id"]:
                shifts.append(
                    {
                        "shift_id": f"SFT-{p_id}-{shift_counter:05d}",
                        "plant_id": p_id,
                        "operator_id": f"OPR-{self.rng.integers(100, 999)}",
                        "start_time": cur,
                        "end_time": cur + timedelta(hours=8),
                    }
                )
            shift_counter += 1
            cur += timedelta(hours=8)
        return pd.DataFrame(shifts)

    def generate_events(
        self, df_machines, df_alarm_defs, df_shifts, df_interlocks
    ):
        total_seconds = int((self.end_dt - self.start_dt).total_seconds())
        m_ids = df_machines["machine_id"].values
        def_ids = df_alarm_defs["alarm_def_id"].values
        def_lookup = df_alarm_defs.set_index("alarm_def_id").to_dict("index")
        m_lookup = df_machines.set_index("machine_id").to_dict("index")

        # Nuisance machines: 5% of machines trigger 40% of alarms
        nuisance_machines = self.rng.choice(
            m_ids, size=max(1, int(len(m_ids) * 0.05)), replace=False
        )

        alarm_records = []
        incidents = []
        acks = []
        actions = []

        m_alarm_counters = {m_id: 0 for m_id in m_ids}
        inc_counter = 1

        timestamps = self.rng.integers(0, total_seconds, size=self.target_alarms)
        timestamps.sort()

        for offset in timestamps:
            ev_time = self.start_dt + timedelta(seconds=int(offset))

            # Select machine (skewed to nuisance machines)
            if self.rng.random() < 0.40:
                m_id = self.rng.choice(nuisance_machines)
            else:
                m_id = self.rng.choice(m_ids)

            m_alarm_counters[m_id] += 1
            a_id = f"ALM-{m_id}-{m_alarm_counters[m_id]:06d}"
            d_id = self.rng.choice(def_ids)
            d_meta = def_lookup[d_id]
            sev = d_meta["severity"]

            alarm_records.append(
                {
                    "alarm_id": a_id,
                    "machine_id": m_id,
                    "alarm_def_id": d_id,
                    "timestamp": ev_time,
                    "severity": sev,
                    "is_flood": False,
                }
            )

            # Acknowledgement logic (92% acknowledged normally)
            if self.rng.random() < 0.92:
                # Add SLA latency
                delay = self.rng.exponential(scale=d_meta["ack_sla_sec"] * 0.5)
                # 5% delayed acknowledgements
                if self.rng.random() < 0.05:
                    delay += d_meta["ack_sla_sec"] * 2.0
                ack_time = ev_time + timedelta(seconds=int(delay))
                acks.append(
                    {
                        "ack_id": f"ACK-{a_id}-01",
                        "alarm_id": a_id,
                        "ack_time": ack_time,
                        "operator_id": f"OPR-{self.rng.integers(100, 999)}",
                    }
                )

            # High severity + critical conditions trigger an Incident
            if sev == "CRITICAL" and self.rng.random() < 0.35:
                inc_id = f"INC-2026-{inc_counter:06d}"
                inc_counter += 1
                inc_time = ev_time + timedelta(seconds=int(self.rng.integers(5, 60)))
                incidents.append(
                    {
                        "incident_id": inc_id,
                        "machine_id": m_id,
                        "zone_id": m_lookup[m_id]["zone_id"],
                        "triggering_alarm_id": a_id,
                        "timestamp": inc_time,
                        "severity": self.rng.choice(
                            ["MINOR", "MAJOR", "CRITICAL"], p=[0.2, 0.5, 0.3]
                        ),
                    }
                )

                # Corrective Action
                act_resolved = inc_time + timedelta(
                    minutes=int(self.rng.integers(15, 240))
                )
                act_verified = act_resolved + timedelta(
                    minutes=int(self.rng.integers(10, 60))
                )
                actions.append(
                    {
                        "action_id": f"ACT-{inc_id}-01",
                        "incident_id": inc_id,
                        "action_state": "VERIFIED",
                        "resolved_time": act_resolved,
                        "verification_time": act_verified,
                        "notes": "Component inspected, interlock reset, perimeter re-tested.",
                    }
                )

        df_alarms = pd.DataFrame(alarm_records)
        df_acks = pd.DataFrame(acks)
        df_incidents = pd.DataFrame(incidents)
        df_actions = pd.DataFrame(actions)

        return df_alarms, df_acks, df_incidents, df_actions
