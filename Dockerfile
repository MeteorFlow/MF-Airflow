# FROM apache/airflow:2.9.1-python3.11
FROM python:3.11.9-slim-bookworm
# ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64/
USER root
RUN apt update && \
    apt install -y --no-install-recommends --fix-missing build-essential pkg-config libhdf5-dev

ENV AIRFLOW_HOME=/opt/airflow
WORKDIR /opt/airflow
COPY --chown=airflow requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=airflow airflow/webserver_config.py .
COPY --chown=airflow airflow/dags ./dags