import datetime
import json
from datetime import timedelta
from pathlib import Path
from pprint import pprint

import slugify as slugify
from airflow import DAG
from airflow.operators.bash import BashOperator

from airflow.models.baseoperator import BaseOperator
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


cfg, dag_type = load_cfg_for_dagfile(__file__)
if not cfg:
    exit(-1)

# pprint(cfg)
# import time
# time.sleep(2)



def tree(l: list) -> list:
    if not len(l):
        return

    nextlevel = []
    if l:
        left = l.pop(0)

        # nextlevel.append([f"{left=}", []])
        nextlevel.append([left, []])
    if l:
        right = l.pop(0)
        # nextlevel.append([f"{right=}", []])
        nextlevel.append([right, []])

    if len(l):
        for idx, n in enumerate(nextlevel):
            sub = tree(l)
            if sub:
                nextlevel[idx][1].append(sub)
            else:
                del nextlevel[idx][1]  # remove empty list
    else:
        for idx, n in enumerate(nextlevel):
            del nextlevel[idx][1]  # remove empty list

    if nextlevel:
        while isinstance(nextlevel, list) and len(nextlevel) == 1:
            nextlevel = nextlevel[0]

        return nextlevel
    return



def unwrap(l):
    # print(f"unwrapping {l} --> ", end='')
    if not isinstance(l, list):
        pass
    else:
        while isinstance(l, list) and len(l) == 1:
            l = unwrap(l[0])
    # print(f" {l}")
    return l


def emit(s:BaseOperator, b:BaseOperator, e:BaseOperator):
    out = f"{s} >> {b}"
    b.set_upstream(s)
    if e:
        out += f" {e}"
        e.set_upstream(b)
    print(out)



def ct2(start, t, end, indent=0):
    l = unwrap(t)
    if not isinstance(l, list):
        emit(start, l, end)

    else:
        for n in l:
            if len(n[1:]):
                ct2(start, n[0], None, indent=indent + 3)
            else:
                ct2(start, n[0], end, indent=indent + 3)
            for m in n[1:]:
                ct2(n[0], m, end, indent=indent + 3)


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
        t = tree(steps)  # consumes steps
        # t = t[0]
        print(t)

        # start >> preconditions >> t >> end
        start >> preconditions
        ct2(preconditions, t, end)

    else:
        # serial
        start >> preconditions

        last_step = preconditions
        for step in steps:
            step.set_upstream(last_step)
            last_step = step

        step >> end
