"""
Main entry point. Generates data, injects edge cases, exports schemas,
validates datasets, and runs the analytics suite.
"""

import os
from tabulate import tabulate
from src.analytics import SafetyEventAnalytics
from src.anomalies import AnomalyInjector
from src.generator import SyntheticDataGenerator
from src.validator import DataValidator


def main():
    print("=" * 70)
    print("OT/IT INDUSTRIAL SAFETY ANALYTICS: PIPELINE RUN")
    print("=" * 70)

    # 1. Execute deterministic generation
    print("\n[Step 1] Generating Master and Transaction Tables...")
    gen = SyntheticDataGenerator(seed=20261022, target_alarms=50000)
    df_plants, df_zones, df_machines, df_interlocks, df_defs = gen.generate_masters()
    df_shifts = gen.generate_shifts(df_plants)
    df_alarms, df_acks, df_incidents, df_actions = gen.generate_events(
        df_machines, df_defs, df_shifts, df_interlocks
    )

    # 2. Inject labelled edge cases
    print("[Step 2] Injecting Labelled Anomaly Edge Cases...")
    injector = AnomalyInjector(rng=gen.rng)
    (
        df_alarms,
        df_acks,
        df_interlocks,
        df_incidents,
        df_actions,
        df_ground_truth,
    ) = injector.inject_all(
        df_alarms, df_acks, df_interlocks, df_incidents, df_actions
    )

    # 3. Export datasets
    os.makedirs("output", exist_ok=True)
    df_plants.to_csv("output/plants.csv", index=False)
    df_zones.to_csv("output/safety_zones.csv", index=False)
    df_machines.to_csv("output/machines.csv", index=False)
    df_interlocks.to_csv("output/interlocks.csv", index=False)
    df_defs.to_csv("output/alarm_definitions.csv", index=False)
    df_shifts.to_csv("output/operator_shifts.csv", index=False)
    df_alarms.to_csv("output/alarm_events.csv", index=False)
    df_acks.to_csv("output/acknowledgements.csv", index=False)
    df_incidents.to_csv("output/incidents.csv", index=False)
    df_actions.to_csv("output/corrective_actions.csv", index=False)
    df_ground_truth.to_csv("output/ground_truth.csv", index=False)
    print("Exported CSV datasets and ground_truth.csv to /output.")

    # 4. Run Validator
    print("\n[Step 3] Running Automated Validation Suite...")
    validator = DataValidator()
    val_report = validator.validate(
        df_plants,
        df_zones,
        df_machines,
        df_interlocks,
        df_defs,
        df_alarms,
        df_acks,
        df_incidents,
        df_actions,
    )
    print(tabulate(val_report, headers="keys", tablefmt="psql", showindex=False))

    # 5. Run Analytics
    print("\n[Step 4] Running Root-Cause & Repeated Unsafe Condition Analytics...")
    analytics = SafetyEventAnalytics(
        df_alarms, df_acks, df_incidents, df_actions, df_defs
    )
    nuisance = analytics.find_nuisance_alarm_hotspots()
    print("\n--- Top Chronic Nuisance Assets ---")
    print(tabulate(nuisance.head(5), headers="keys", tablefmt="psql", showindex=False))

    repeated_hazards = analytics.find_repeated_unsafe_conditions(min_incidents=2)
    print("\n--- Repeated Unsafe Conditions (Incident Clusters) ---")
    print(tabulate(repeated_hazards.head(5), headers="keys", tablefmt="psql", showindex=False))

    sla_metrics = analytics.calculate_ack_sla_metrics()
    print("\n--- ISA-18.2 SLA Compliance Breakdown ---")
    print(tabulate(sla_metrics, headers="keys", tablefmt="psql", showindex=False))


if __name__ == "__main__":
    main()
