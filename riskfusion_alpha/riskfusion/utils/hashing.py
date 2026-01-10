import pandas as pd
import hashlib
import json
from pathlib import Path
from typing import Union, List, Any

def save_parquet(df: pd.DataFrame, path: Union[str, Path], partition_cols: List[str] = None):
    """Save dataframe to parquet with optimal settings."""
    path = str(path)
    # Ensure directory exists
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    if partition_cols:
        df.to_parquet(path, partition_cols=partition_cols, engine='pyarrow', compression='snappy')
    else:
        df.to_parquet(path, engine='pyarrow', compression='snappy')

def load_parquet(path: Union[str, Path]) -> pd.DataFrame:
    """Load parquet file."""
    return pd.read_parquet(path, engine='pyarrow')

def compute_hash(obj: Any) -> str:
    """Compute stable hash for an object (df, dict, file)."""
    if isinstance(obj, pd.DataFrame):
        # Hash dataframe content
        return hashlib.sha256(pd.util.hash_pandas_object(obj, index=True).values).hexdigest()
    elif isinstance(obj, dict):
        # Hash dictionary
        encoded = json.dumps(obj, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()
    elif isinstance(obj, (str, Path)):
        # If it's a file path, hash the file content
        p = Path(obj)
        if p.exists() and p.is_file():
            return hashlib.sha256(p.read_bytes()).hexdigest()
        else:
            return hashlib.sha256(str(obj).encode()).hexdigest()
    else:
        return hashlib.sha256(str(obj).encode()).hexdigest()


