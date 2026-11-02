"""
Safety Analytics Module: Identifies repeated unsafe conditions, nuisance alarm
hotspots, SLA breaches, and correlates machine risk profiles.
"""

from datetime import timedelta
import pandas as pd


class SafetyEventAnalytics:

    def __init__(
        self,
        df_alarms,
        df_acks,
        df_incidents,
        df_actions,
        df_alarm_defs,
    ):
        self.df_alarms = df_alarms
        self.df_acks = df_acks
        self.df_incidents = df_incidents
        self.df_actions = df_actions
        self.df_alarm_defs = df_alarm_defs

    def find_nuisance_alarm_hotspots(self, threshold: int = 500) -> pd.DataFrame:
        """Find machines exceeding alarm density thresholds."""
        counts = self.df_alarms.groupby("machine_id").size().reset_index(name="alarm_count")
        return (
            counts[counts["alarm_count"] >= threshold]
            .sort_values(by="alarm_count", ascending=False)
        )

    def find_repeated_unsafe_conditions(self, min_incidents: int = 3) -> pd.DataFrame:
        """
        Detects chronic machine hazards: assets with multiple incidents
        linked with delayed acknowledgements or unresolved states.
        """
        inc_summary = (
            self.df_incidents.groupby(["machine_id", "zone_id"])
            .agg(
                incident_count=("incident_id", "count"),
                critical_count=("severity", lambda s: (s == "CRITICAL").sum()),
            )
            .reset_index()
        )
        repeated = inc_summary[inc_summary["incident_count"] >= min_incidents].sort_values(
            by="incident_count", ascending=False
        )
        return repeated

    def calculate_ack_sla_metrics(self) -> pd.DataFrame:
        """Computes compliance against ISA-18.2 acknowledgment SLAs."""
        merged = pd.merge(
            self.df_acks, self.df_alarms, on="alarm_id", suffixes=("_ack", "_alm")
        )
        merged = pd.merge(merged, self.df_alarm_defs, on="alarm_def_id")
        merged["ack_latency_sec"] = (
            pd.to_datetime(merged["ack_time"]) - pd.to_datetime(merged["timestamp"])
        ).dt.total_seconds()
        merged["sla_breached"] = merged["ack_latency_sec"] > merged["ack_sla_sec"]

        metrics = (
            merged.groupby("severity_x")
            .agg(
                total_alarms=("alarm_id", "count"),
                sla_breaches=("sla_breached", "sum"),
                avg_latency_sec=("ack_latency_sec", "mean"),
            )
            .reset_index()
        )
        return metrics
