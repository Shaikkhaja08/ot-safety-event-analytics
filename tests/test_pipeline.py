"""
Pytest Verification Suite.
Run with: pytest tests/test_pipeline.py -v
"""

import hashlib
import pandas as pd
from src.generator import SyntheticDataGenerator


def get_df_hash(df: pd.DataFrame) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values).hexdigest()


def test_seed_reproducibility():
    """Verify identical dataframes generated twice using fixed seed."""
    gen1 = SyntheticDataGenerator(seed=20261022, target_alarms=1000)
    m1, _, _, _, _ = gen1.generate_masters()

    gen2 = SyntheticDataGenerator(seed=20261022, target_alarms=1000)
    m2, _, _, _, _ = gen2.generate_masters()

    assert get_df_hash(m1) == get_df_hash(m2)
    assert len(m1) == len(m2)


def test_entity_cardinality():
    """Verify required scale targets."""
    gen = SyntheticDataGenerator(
        seed=20261022, num_plants=4, num_machines=60, num_defs=200, target_alarms=5000
    )
    df_plants, df_zones, df_machines, df_interlocks, df_defs = gen.generate_masters()

    assert len(df_plants) == 4
    assert len(df_machines) == 60
    assert len(df_defs) == 200
    assert len(df_zones) == 12  # 3 zones per plant
