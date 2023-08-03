#! env python
import json
import logging
import os
import re
import uuid
from pathlib import Path
import requests

import faker as faker

faker.Faker.seed(0)
fake = faker.Faker()

fact_cache = []
def get_fact():
    global fact_cache
    try:
        fact = fact_cache.pop()
    except IndexError as empty:
        # will get throttled
        fact_url = "https://cat-fact.herokuapp.com/facts"
        data = requests.get(fact_url).json()
        for item in data:
            f = item["text"]
            fact_cache.append(f)
        fact = fact_cache.pop()

    return fact



def main(qty=100, include_external_facts=False):
    config_root = Path("./configs/")
    config_root.mkdir(parents=True, exist_ok=True)

    for i in range(qty):
        name = str(fake.company())
        slug = name.lower().replace(" ", "_").replace(",", "_").replace("-", "_")
        slug = re.sub(r"_{2,}", "_", slug)

        (a, b) = fake.random.randint(2, 7), fake.random.randint(2, 7)
        full_steps = max(a, b)
        incr_steps = min(a, b)

        if include_external_facts:
            description = get_fact()
        else:
            description =f"Config {i+1}"
        cfg = {
            "id": f"Config-{i}",
            "name": name,
            "description": description,
            "src_bucket": f"s3://root/raw/raw-{slug}/",
            "src_pattern": f"*.{fake.file_extension()}",
            "dest_bucket": f"s3://destination/{uuid.uuid4()}",
            "on_fail_notify": fake.ascii_company_email(),
        }

        config_file = config_root / Path(f"./{slug[0]}/{slug}_full.json")
        config_file.parent.mkdir(parents=True, exist_ok=True)
        cfg["steps"] = full_steps
        with config_file.open("w") as fh_config:
            json.dump(cfg, fh_config, indent=2)
        print(f"#{i*2+1}/{qty*2} {config_file} written")
        config_file = config_root / Path(f"./{slug[0]}/{slug}_incremental.json")
        config_file.parent.mkdir(parents=True, exist_ok=True)
        cfg["steps"] = incr_steps
        with config_file.open("w") as fh_config:
            json.dump(cfg, fh_config, indent=2)
        print(f"#{i*2+2}/{qty*2} {config_file} written")


if __name__ == "__main__":
    LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()
    logging.basicConfig(level=LOGLEVEL)
    # main(250, include_external_facts=True)
    #  2.19s user 0.59s system 5% cpu 53.755 total
    #  2.13s user 0.90s system 22% cpu 13.602 total
    # main(1000, include_external_facts=False)
    #  2.96s user 1.22s system 97% cpu 4.267 total
    #  3.04s user 1.28s system 77% cpu 5.573 total
    # Demonstrates why external resources should be gathered in build-time.
    # using external data was faster in terms of user time, but much longer in clock time
    # despite building on 1/4 the number of dags.
    # moving all of the uncertainty to the build phase makes the run-time DAGs constant time.
    # main(40, include_external_facts=False)  # max for worst with .1 sec delay
    # main(1200, include_external_facts=False)  # max for worst with no delay
    #main(2200, include_external_facts=False) # took 4:23 to load these.   But no errors, and risk is spread out.
    # main(5000)
    main(50)
