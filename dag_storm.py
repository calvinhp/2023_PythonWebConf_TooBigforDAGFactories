import concurrent.futures
import datetime
import time

import httpx

parallel = 25
storm_size = 100

# get list of enabled dags
# curl http://localhost:8080/api/v1/dags\?only_active\=True --user "airflow:airflow"
active_dag_resp = httpx.get(
    # "http://localhost:8080/api/v1/dags?only_active=true", auth=("airflow", "airflow")
    # "http://localhost:8080/api/v1/dags?paused=0",  # new in 2.6
    "http://localhost:8080/api/v1/dags?limit=10000",  # wont go past 100?
    auth=("airflow", "airflow"),
)
active_dag_data = active_dag_resp.json()
print(active_dag_data)
total_entries = active_dag_data["total_entries"]


def get_page(page_num, page_size=100):
    print(f"get_page({page_num}, {page_size})")
    get_dags_page_res = httpx.get(
        f"http://localhost:8080/api/v1/dags?limit={page_size}&offset={page_num * page_size}",
        auth=("airflow", "airflow"),
    )
    return get_dags_page_res


with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
    futures = []
    print(f"total_entries: {total_entries} -> {total_entries // 100} pages")
    for page in range(1, total_entries // 100 + 1):
        futures.append(executor.submit(get_page, page, 100))

    # work with the results as they come in, though possible out of order.
    for future in concurrent.futures.as_completed(futures):
        response = future.result()  # This will give you the response of httpx.post
        print(response)
        active_dag_data["dags"].extend(response.json()["dags"])


active_dag_ids = [
    d["dag_id"] for d in active_dag_data["dags"] if d["is_paused"] == False
]
print(f"active_dag_ids: {active_dag_ids}")


def post_dag(dag_id, i):
    print(f"post_dag({dag_id}, {i})")

    run_dts = datetime.datetime.utcnow().isoformat()
    suffix = str(time.time()).replace(".", "")
    return httpx.post(
        f"http://localhost:8080/api/v1/dags/{dag_id}/dagRuns",
        auth=("airflow", "airflow"),
        json={
            "dag_run_id": f"{dag_id}-run-{i}-{suffix}",  # must also be unique
            # "logical_date": run_dts,
            # "execution_date": run_dts,  # deprecated but must be included in logical_date is used.
        },
        timeout=30,
    )


# for each dag, kick it off n times.
if not parallel:
    for dag_id in active_dag_ids:
        for i in range(storm_size):
            res = post_dag(dag_id, i)
            print(res)

# or kick them all off at once
else:
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = []
        for dag_id in active_dag_ids:
            for i in range(storm_size):
                futures.append(executor.submit(post_dag, dag_id, i))

        # Optional: if you want to work with the results as they come in
        for future in concurrent.futures.as_completed(futures):
            response = future.result()  # This will give you the response of httpx.post
            # do something with response if you want
            print(response)
