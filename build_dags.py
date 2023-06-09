#! env python
import shutil
from pathlib import Path
from importlib import import_module

dynamic_dag_file = Path("./gen_dag_from_filename.py")
config_root = Path("./configs/")

dag_root = Path("./dags/")

for config_file in config_root.glob("**/*.json"):
    dag_file_name = dag_root / config_file.relative_to(config_root).with_suffix(".py")
    dag_file_name.parent.mkdir(parents=True, exist_ok=True)
    print(f"copy {dynamic_dag_file} to {dag_file_name}")
    shutil.copy(dynamic_dag_file, dag_file_name)
    # pre-pop the __pycache__ to be delivered as an artifact
    module_name = f"dags.{config_file.stem[0]}.{config_file.stem}"
    m = import_module(module_name)
