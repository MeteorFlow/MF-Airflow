FROM apache/airflow:slim-2.9.1-python3.11
# ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64/
# USER root
# RUN apt update && \
#     apt install -y --no-install-recommends openjdk-17-jre-headless procps

USER airflow

WORKDIR /opt/airflow
COPY --chown=airflow requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=airflow airflow/webserver_config.py .
COPY --chown=airflow airflow/dags ./dags