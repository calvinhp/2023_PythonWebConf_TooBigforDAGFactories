---
title-prefix: Six Feet Up
pagetitle: Too Big for DAG Factories
author: Calvin Hendryx-Parker, CTO, Six Feet Up
author-meta:
    - Calvin Hendryx-Parker
date: Python Web Conf 2023
date-meta: 2023
keywords:
    - Python
    - Airflow
    - Big Data
    - Orchestration
---

# Too Big for DAG Factories? {.semi-filtered data-background-image="images/karsten-wurth-lsJ9jHKIqHg-unsplash.jpg"}
#### Calvin Hendryx-Parker, CTO
#### Six Feet Up


::: notes
Brief intro to how this all started

Pointer to talk from last year
:::


# Why should I care about this talk? {.r-fit-text .semi-filtered data-background-image="images/matt-artz-2dCdOoYDjOQ-unsplash.jpg"}

1. Do you think Airflow might be the wrong tool?
1. Airflow can’t scale to your needs?

# Let's set our intention {data-background-image="images/zac-wolff-ZTbMpMGB_7A-unsplash.jpg"}

~~~
$ python -m this

The Zen of Python, by Tim Peters

Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
Now is better than never.
Although never is often better than *right* now.
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
~~~

# Brief introduction to Airflow {.semi-filtered data-background-image="images/matt-artz-J2R6iK8A6mQ-unsplash.jpg"}

* DAGs
* Operators
* Sensors
* Connections
* Hooks
* Scheduler

::: notes
DAGs are series of tasks made of Operators, Sensors or TaskFlows

Connections and Hooks provide easy access to external systems and APIs
:::

# {.original data-background-image="images/arch-diag-basic.png"}

# Demo the the problem {.semi-filtered data-background-image="images/vivek-kumar-C5HZDAVQwuQ-unsplash.jpg"}

* Create a Dynamic DAG that takes too long to generate
* Airflow can slow down with lot's of DAGs

# Root cause of the problem {.semi-filtered data-background-image="images/venti-views-8RBASNzrrXA-unsplash.jpg"}

::: notes
    1. The dangers of runtime dependencies.
    2. Dynamic DAG generation can start to take longer than the DAG scanning cycle
        1. By sheer numbers that will be generated (just a lot, 1000+)
            1. 1 file that was generating 1000s of dags dynamically and failing the time limit
        2. By making outside API calls during generation (calling App Config for config data)
            1. remove any dag import time externalities
        3. By inefficient code (json5 1000x slowdown)
            1. 1000s of files each generating 1 dag dynamically and failing the time limit
:::

# Solutions {.semi-filtered data-background-image="images/maria-velniceriu-zx7Vg4tkLkU-unsplash.jpg"}

* Start with Dynamic DAGs Factories
* As you scale up you will need to statically generate
* Precompute configurations and data needed during build
* Optimize to run your tasks in parallel

# Wrap up and Questions {.semi-filtered data-background-image="images/justin-casey-7B0D1zO3PoQ-unsplash.jpg"}

## Resources

* [Airflow Docs](https://airflow.apache.org/docs/apache-airflow/stable/index.html)
* Six Feet Up Blog Post -- [Too Big for DAG Factories?](https://sixfeetup.com/blog/too-big-for-dag-factories)

## Find Me 😍

#### <calvin@sixfeetup.com>

🐘 [`@calvinhp@fosstodon.org`](https://fosstodon.org/@calvinhp)  
🐦 [`@calvinhp`](https://twitter.com/calvinhp)

