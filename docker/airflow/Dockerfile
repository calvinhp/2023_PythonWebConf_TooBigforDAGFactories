FROM apache/airflow:2.6.3
USER root
RUN apt update
RUN apt install -y git

# all to install a patched airflow-prometheus-exporter
USER airflow
RUN pip install --upgrade pip
RUN pip install flask-admin
RUN python -m pip install git+https://github.com/KulykDmytro/airflow-prometheus-exporter@master#egg=airflow-prometheus-exporter
# hmm, only up to airflow 2.2
