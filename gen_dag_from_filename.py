import datetime
import json
from datetime import timedelta
from pathlib import Path
from pprint import pprint

import slugify as slugify
from airflow import DAG
from airflow.operators.bash import BashOperator


def load_cfg_for_dagfile(f: str) -> (dict, str):
    file = Path(f)
    root_generator = (
        p for p in (Path("../../configs"), Path("./configs")) if p.exists()
    )
    root = next(root_generator, None)
    if not root:
        print(f"no root in {list(root_generator)}")
        return dict(), None
    # print(f"config root is {root}")

    subdir = Path(file.name[0])

    _parts = file.stem.split("-")
    dag_type = _parts[-1].lower()
    dag_slug = "-".join(_parts[:-1])
    cfg_ext = "json"

    cfg_file = root / subdir / Path(f"{dag_slug}-{dag_type}.{cfg_ext}")
    cfg = json.load(cfg_file.open("r"))

    return cfg, dag_type


cfg, dag_type = load_cfg_for_dagfile(__file__)
if not cfg:
    exit(-1)

# pprint(cfg)

with DAG(
    slugify.slugify(f'{cfg["name"]} - {dag_type}'),
    start_date=datetime.datetime.fromtimestamp(Path(__file__).stat().st_mtime),
    description=cfg["description"],
    default_args={
        "depends_on_past": False,
        "email": [
            cfg["on_fail_notify"],
        ],
        "email_on_failure": True,
        "email_on_retry": False,
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
) as dag:
    start = BashOperator(
        task_id="start",
        bash_command="date",
    )
    preconditions = BashOperator(
        task_id="preconditions",
        bash_command="date",
    )
    end = BashOperator(
        task_id="end-cleanup",
        bash_command="date",
    )

    steps = []
    for step_num in range(cfg["steps"]):
        step = BashOperator(
            task_id=f"Step-{step_num+1}",
            bash_command=f"sleep {2*(step_num+1)}",
        )
        steps.append(step)

    if dag_type == "full":
        # parallel
        start >> preconditions >> steps >> end

    else:
        # serial
        start >> preconditions

        last_step = preconditions
        for step in steps:
            step.set_upstream(last_step)
            last_step = step

        step >> end
