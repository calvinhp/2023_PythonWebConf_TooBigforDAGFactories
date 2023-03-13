#! env python
import json
import logging
import os
import re
from pathlib import Path

import faker as faker
# from faker.providers import company, internet, file

faker.Faker.seed(0)
fake = faker.Faker()
import uuid

def main():
    for i in range(1000):
        name = str(fake.company())
        slug = name.lower().replace(" ","-").replace(",", "-")
        slug = re.sub(r'-{2,}', '-', slug)


        cfg = {
            "id": f"Config-{i}",
            "name": name,
            "src_bucket": f"s3://root/raw/raw-{slug}/",
            "src_pattern": f"*.{fake.file_extension()}",
            "dest_bucket": f"s3://destination/{uuid.uuid4()}",
            "on_fail_notify": fake.ascii_company_email(),
        }

        config_file = Path(f"./{slug[0]}/{slug}.json")
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with config_file.open("w") as fh_config:
            json.dump(cfg, fh_config, indent=2)


if __name__ == "__main__":
    LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
    logging.basicConfig(level=LOGLEVEL)
    main()
