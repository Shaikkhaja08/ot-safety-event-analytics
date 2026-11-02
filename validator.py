"""
Validation Suite checking integrity, foreign keys, timelines, and lifecycle assertions.
"""

import pandas as pd


class DataValidator:

    def __init__(self):
        self.validation_results = []

    def log(self, check_name: str, passed: bool, details: str):
        self.validation_results.append(
            {"check": check_name, "status": "PASS" if passed else "FAIL", "details": details}
        )

    def validate(
        self,
        df_plants,
        df_zones,
        df_machines,
        df_interlocks,
        df_alarm_defs,
        df_alarms,
        df_acks,
        df_incidents,
        df_actions,
    ):
        # 1. Primary Key Uniqueness
        for name, df, pk in [
            ("Plant", df_plants, "plant_id"),
            ("SafetyZone", df_zones, "zone_id"),
            ("Machine", df_machines, "machine_id"),
            ("Interlock", df_interlocks, "interlock_id"),
            ("AlarmDef", df_alarm_defs, "alarm_def_id"),
            ("Incident", df_incidents, "incident_id"),
            ("CorrectiveAction", df_actions, "action_id"),
        ]:
            is_uniq = df[pk].is_unique
            self.log(f"PK Uniqueness: {name}", is_uniq, f"Total: {len(df)}, Unique: {df[pk].nunique()}")

        # 2. Foreign Key Validations
        valid_plants = set(df_plants["plant_id"])
        valid_zones = set(df_zones["zone_id"])
        valid_machines = set(df_machines["machine_id"])
        valid_defs = set(df_alarm_defs["alarm_def_id"])

        mch_fk_valid = df_machines["plant_id"].isin(valid_plants).all()
        self.log("FK: Machine -> Plant", mch_fk_valid, "All machines reference valid plants")

        int_mch_fk = df_interlocks["machine_id"].isin(valid_machines).all()
        int_zne_fk = df_interlocks["zone_id"].isin(valid_zones).all()
        self.log("FK: Interlock -> Machine/Zone", int_mch_fk and int_zne_fk, "Interlocks resolve to parents")

        alm_def_fk = df_alarms["alarm_def_id"].isin(valid_defs).all()
        alm_mch_fk = df_alarms["machine_id"].isin(valid_machines).all()
        self.log("FK: Alarm -> Def/Machine", alm_def_fk and alm_mch_fk, "Alarms map to schema items")

        # 3. Anomaly Exposure Checks (Chronological and Lifecycle)
        merged_ack = pd.merge(df_acks, df_alarms, on="alarm_id", suffixes=("_ack", "_alm"))
        bad_acks = merged_ack[merged_ack["ack_time"] < merged_ack["timestamp"]]
        self.log(
            "Anomaly Verification: ACK_BEFORE_ALARM",
            len(bad_acks) > 0,
            f"Exposed {len(bad_acks)} records where ack precedes alarm",
        )

        invalid_interlocks = df_interlocks[
            ~df_interlocks["state"].isin(["ENGAGED", "DISENGAGED", "FAULT"])
        ]
        self.log(
            "Anomaly Verification: INTERLOCK_STATE_IMPOSSIBLE",
            len(invalid_interlocks) > 0,
            f"Identified {len(invalid_interlocks)} illegal interlock states",
        )

        unverified_actions = df_actions[
            (df_actions["action_state"] == "VERIFIED")
            & (df_actions["verification_time"].isna())
        ]
        self.log(
            "Anomaly Verification: ACTION_CLOSED_WITHOUT_VERIFICATION",
            len(unverified_actions) > 0,
            f"Identified {len(unverified_actions)} unverified closed actions",
        )

        return pd.DataFrame(self.validation_results)
