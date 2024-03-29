FROM apache/airflow:slim-2.8.1-python3.11
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64/
USER root
RUN apt update && \
    apt install -y --no-install-recommends openjdk-17-jre-headless procps

USER airflow

WORKDIR /opt/airflow
COPY --chown=airflow requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installing customized library
# COPY --chown=airflow rs_airflow rs_airflow
# RUN pip install -e ./rs_airflow

COPY --chown=airflow airflow/webserver_config.py .
# COPY --chown=airflow airflow/dags ./dags