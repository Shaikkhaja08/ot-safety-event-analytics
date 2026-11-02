"""
Injects labeled negative edge cases and outputs a strictly isolated ground truth store.
Edge cases:
1. Acknowledgement before alarm
2. Interlock state impossible
3. Safety incident lacks triggering context
4. Alarm flood duplicated by replay
5. Action closed without verification
"""

from datetime import timedelta
import pandas as pd


class AnomalyInjector:

    def __init__(self, rng):
        self.rng = rng
        self.ground_truth = []

    def inject_all(
        self,
        df_alarms,
        df_acks,
        df_interlocks,
        df_incidents,
        df_actions,
    ):
        df_alarms = df_alarms.copy()
        df_acks = df_acks.copy()
        df_interlocks = df_interlocks.copy()
        df_incidents = df_incidents.copy()
        df_actions = df_actions.copy()

        # 1. Edge Case: Acknowledgement timestamp precedes Alarm timestamp
        ack_targets = df_acks.sample(n=15, random_state=42).index
        for idx in ack_targets:
            parent_alarm_id = df_acks.loc[idx, "alarm_id"]
            orig_alarm_time = df_alarms.loc[
                df_alarms["alarm_id"] == parent_alarm_id, "timestamp"
            ].values[0]
            corrupt_ack_time = pd.to_datetime(orig_alarm_time) - timedelta(
                seconds=120
            )
            df_acks.loc[idx, "ack_time"] = corrupt_ack_time
            self.ground_truth.append(
                {
                    "entity": "Acknowledgement",
                    "record_id": df_acks.loc[idx, "ack_id"],
                    "issue_type": "ACK_BEFORE_ALARM",
                    "description": f"Ack occurs at {corrupt_ack_time} prior to alarm {orig_alarm_time}",
                }
            )

        # 2. Edge Case: Interlock state impossible (machine running but interlock broken/disengaged)
        int_targets = df_interlocks.sample(n=10, random_state=42).index
        for idx in int_targets:
            df_interlocks.loc[idx, "state"] = "INVALID_UNKNOWN_STATE"
            self.ground_truth.append(
                {
                    "entity": "Interlock",
                    "record_id": df_interlocks.loc[idx, "interlock_id"],
                    "issue_type": "INTERLOCK_STATE_IMPOSSIBLE",
                    "description": "Invalid enum state outside physical safety bounds",
                }
            )

        # 3. Edge Case: Incident lacks triggering context (points to non-existent alarm ID)
        inc_targets = df_incidents.sample(n=10, random_state=42).index
        for idx in inc_targets:
            ghost_id = "ALM-MCH-999-999999"
            df_incidents.loc[idx, "triggering_alarm_id"] = ghost_id
            self.ground_truth.append(
                {
                    "entity": "Incident",
                    "record_id": df_incidents.loc[idx, "incident_id"],
                    "issue_type": "ORPHAN_INCIDENT_NO_CONTEXT",
                    "description": f"FK violation: References non-existent trigger {ghost_id}",
                }
            )

        # 4. Edge Case: Replay attack / Sensor echo (Alarm flood duplicated)
        flood_subset = df_alarms.sample(n=30, random_state=42).copy()
        for idx, row in flood_subset.iterrows():
            self.ground_truth.append(
                {
                    "entity": "AlarmEvent",
                    "record_id": row["alarm_id"],
                    "issue_type": "ALARM_FLOOD_REPLAY_DUPLICATE",
                    "description": f"Duplicated duplicate record detected via replay for {row['alarm_id']}",
                }
            )
        df_alarms = pd.concat([df_alarms, flood_subset], ignore_index=True)

        # 5. Edge Case: Action closed/verified without verification timestamp
        act_targets = df_actions.sample(n=12, random_state=42).index
        for idx in act_targets:
            df_actions.loc[idx, "verification_time"] = pd.NaT
            df_actions.loc[idx, "action_state"] = "VERIFIED"
            self.ground_truth.append(
                {
                    "entity": "CorrectiveAction",
                    "record_id": df_actions.loc[idx, "action_id"],
                    "issue_type": "ACTION_CLOSED_WITHOUT_VERIFICATION",
                    "description": "Lifecycle state marked VERIFIED without recorded signoff timestamp",
                }
            )

        df_gt = pd.DataFrame(self.ground_truth)
        return df_alarms, df_acks, df_interlocks, df_incidents, df_actions, df_gt
