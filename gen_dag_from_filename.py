import asyncio
import datetime
import json
import time
from datetime import timedelta
from pathlib import Path
from pprint import pprint
from typing import Any, AsyncIterator, Dict, Iterator, AnyStr, Tuple

import httpx as httpx
import requests as requests
import slugify as slugify
from airflow import DAG
from airflow.models.baseoperator import BaseOperator
from airflow.operators.bash import BashOperator
from airflow.triggers.base import BaseTrigger, TriggerEvent


def fullname(o: object) -> AnyStr:
    """
    Return the fully-qualified (dotted form) name of the object from its class.
    Serializers often need to know the full name of a class, so this can compute it
    from an object.
    """
    klass = o.__class__
    module = klass.__module__
    if module == "builtins":
        return klass.__qualname__
    return module + "." + klass.__qualname__


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


def emit(s: BaseOperator, b: BaseOperator, e: BaseOperator):
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


class BlockingRemoteOperator(BaseOperator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remote_base_url = kwargs.get("remote_base_url", "http://mock-api:5000/")

    def execute(self, context):
        print(f"RemoteOperator.execute({self})")
        self.submit_to_remote(context)
        result = self.wait_for_remote(context)
        return result

    def get_job_id(self, context):
        dag_id = self.dag_id
        task_id = self.task_id
        run_id = context.get("run_id")
        job_id = f"{dag_id}:{task_id}:{run_id}"
        return job_id

    def submit_to_remote(self, context):
        print(f"RemoteOperator.submit_remote({self})")
        response = requests.get(self.remote_base_url + "submit/" + self.get_job_id(context))
        result = response.content.decode("utf-8")
        return result

    def wait_for_remote(self, context):
        result = None
        while result in ("Running", None):
            print(f"RemoteOperator.wait_for_remote({self}) - {result}")
            if result != "Complete":
                time.sleep(1)
            result = self.poll_remote(context)
            print(result)

        return result

    def poll_remote(self, context):
        print(f"RemoteOperator.poll_remote({self})")
        response = requests.get(self.remote_base_url + "status/" + self.get_job_id(context))
        result = response.content.decode("utf-8")
        return result


class DeferredRemoteOperator(BlockingRemoteOperator):
    """
    Synchonous job submittion, but asynchronous job completion polling via Trigger.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self, context):
        print(f"DeferredRemoteOperator.execute({self})")
        submit_result = self.submit_to_remote(context)

        trigger = DeferrableRemoteTrigger(
            base_url=self.remote_base_url,
            task_id=self.task_id,
            dag_id=self.dag_id,
            job_id=self.get_job_id(context),
            submmit_result=submit_result,
        )
        self.defer(
            trigger=trigger,
            method_name="execute_complete",
            kwargs={},
            timeout=datetime.timedelta(minutes=2),
        )
        # execution stops here and frees up the worker
        # the trigger will asynchronously poll for completion then call back to execute_complete

    def execute_complete(self, context, event=None):
        print(f"DeferredRemoteOperator.execute_complete({self})")
        return


class DeferrableRemoteTrigger(BaseTrigger):
    def __init__(
        self,
        *args,
        base_url=None,
        job_id=None,
        dag_id=None,
        submit_result=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        super().__init__()
        self.base_url = base_url
        self.job_id = job_id
        self.dag_id = dag_id
        self.submit_result = submit_result

    def serialize(self) -> Tuple[str, Dict[str, Any]]:
        return (
            fullname(self),
            {
                "base_url": self.base_url,
                "job_id": self.job_id,
                "dag_id": self.run_id,
                "submit_result": self.submit_result,
            },
        )

    async def run(self) -> Iterator["TriggerEvent"]:
        while True:
            async with httpx.AsyncClient() as client:  # TODO: aiohttp is likely even faster here
                response = await client.get(self.base_url + "status/" + self.job_id)
                print(response.text)
                result = response.text

            print(f"DeferrableRemoteTrigger.run({self}) - {result}")

            if result == "complete":
                print(f"DeferrableRemoteTrigger.run({self}) - complete")
                yield TriggerEvent(result)
                break

            else:
                print(f"DeferrableRemoteTrigger.run({self}) - looping after 1 second.")
                yield TriggerEvent(result)
                await asyncio.sleep(1)


# class AsyncRemoteTrigger(DeferrableRemoteTrigger):
#
#     def serialize(self) -> Tuple[str, Dict[str, Any]]:
#         return (
#             "dags.AsyncRemoteTrigger",  # TODO: use fully qualified name
#             {
#                 "job_id": self.job_id,
#                 "dag_id": self.run_id,
#             },
#         )
#
#     async def run(self) -> AsyncIterator["TriggerEvent"]:
#         print(f"AsyncRemoteOperator.run({self})")
#         result = None
#         while self.moment > timezone.utcnow():
#             self.wait_for_remote()
#             await asyncio.sleep(1)
#         yield TriggerEvent(self.moment)

with DAG(
    slugify.slugify(f'{cfg["name"]} - {dag_type}'),
    start_date=datetime.datetime.fromtimestamp(Path(__file__).stat().st_mtime),
    description=cfg["description"],
    schedule=None,
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
        step = BlockingRemoteOperator(
        # step=DeferredRemoteOperator(
                task_id=f"Step-{step_num+1}",
            # bash_command=f"sleep {2*(step_num+1)}",
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
