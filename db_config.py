from pathlib import Path

import yaml


def load_db_config():
    project_root = Path(__file__).resolve().parent
    candidate_paths = [
        project_root / "ECommerce-Grocery-Store" / "database.yaml",
        project_root / "database.yaml",
        project_root / "database copy.yaml",
    ]

    for config_path in candidate_paths:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            if config:
                return config

    searched = ", ".join(str(p) for p in candidate_paths)
    raise FileNotFoundError(f"Database config file not found. Checked: {searched}")