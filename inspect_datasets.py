import os
import json
import pandas as pd

datasets_dir = "./datasets"

for ds_name in os.listdir(datasets_dir):
    ds_path = os.path.join(datasets_dir, ds_name)
    print(f"\n{'='*60}")
    print(f"📦 DATASET: {ds_name}")
    print(f"{'='*60}")
    
    # Find all data files
    for root, dirs, files in os.walk(ds_path):
        for f in files:
            if f.endswith(('.parquet', '.json', '.jsonl', '.csv')):
                fpath = os.path.join(root, f)
                rel_path = os.path.relpath(fpath, ds_path)
                print(f"\n📄 File: {rel_path}")
                
                try:
                    if f.endswith('.parquet'):
                        df = pd.read_parquet(fpath)
                        print(f"   Rows: {len(df)}, Columns: {list(df.columns)}")
                        print(f"   Sample row (first 500 chars per field):")
                        for col in df.columns:
                            val = str(df[col].iloc[0])[:500]
                            print(f"   - {col}: {val}")
                    elif f.endswith('.json'):
                        with open(fpath) as fp:
                            data = json.load(fp)
                        if isinstance(data, list):
                            print(f"   Items: {len(data)}")
                            if data:
                                print(f"   Keys: {list(data[0].keys()) if isinstance(data[0], dict) else type(data[0])}")
                                print(f"   Sample: {str(data[0])[:500]}")
                        elif isinstance(data, dict):
                            print(f"   Keys: {list(data.keys())}")
                    elif f.endswith('.jsonl'):
                        with open(fpath) as fp:
                            first_line = fp.readline()
                        print(f"   Sample: {first_line[:500]}")
                    elif f.endswith('.csv'):
                        df = pd.read_csv(fpath)
                        print(f"   Rows: {len(df)}, Columns: {list(df.columns)}")
                except Exception as e:
                    print(f"   ⚠️  Error reading: {e}")
