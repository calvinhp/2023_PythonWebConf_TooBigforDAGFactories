import datetime
import json
import logging
from datetime import timedelta
from pathlib import Path

import slugify as slugify
from airflow import DAG
from airflow.operators.bash import BashOperator

log = logging.getLogger("airflow")
log.setLevel(logging.INFO)
log.info("worst_case_factory  :)")


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

    _parts = file.stem.split("_")
    dag_type = _parts[-1].lower()
    dag_slug = "_".join(_parts[:-1])
    cfg_ext = "json"

    cfg_file = root / subdir / Path(f"{dag_slug}_{dag_type}.{cfg_ext}")
    cfg = json.load(cfg_file.open("r"))

    return cfg, dag_type


config_root = Path("/opt/airflow/configs")

for config_file in config_root.glob("**/*.json"):
    for dag_type in ("full", "incremental"):
        cfg = json.loads(config_file.read_text())

        # worst case scenario: an external dependency that has to be fetched over the net.
        # simulated as a delay
        import time

        time.sleep(0.10)
        
        # with this delay, I max out at about 40 configs, 80 dags
        # without it, this maxes at about 1200 configs, 2400 dags
        """
        
File Path                                  PID  Runtime      # DAGs    # Errors  Last Runtime    Last Run
---------------------------------------  -----  ---------  --------  ----------  --------------  -------------------
/opt/airflow/dags/worst_case_factory.py    109  3.05s          2306           0  27.15s          2023-03-15T00:04:13
================================================================================
[2023-03-15T00:05:17.089+0000] {manager.py:854} INFO - 
================================================================================
DAG File Processing Stats

File Path                                  PID  Runtime      # DAGs    # Errors  Last Runtime    Last Run
---------------------------------------  -----  ---------  --------  ----------  --------------  -------------------
/opt/airflow/dags/worst_case_factory.py                        2306           0  18.42s          2023-03-15T00:05:02
================================================================================
        """
        # keep in mind, the tine can vary.   That 27.15s was 3 seconds away from airflow removing all of them

        dag_id = slugify.slugify(f'{cfg["name"]}_{dag_type}', separator="_")
        with DAG(
            dag_id,
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

            log.info(f"{dag_id} = {dag}")
            globals()[dag_id] = dag
            globals().pop('dag')

log.info(str(globals()))
