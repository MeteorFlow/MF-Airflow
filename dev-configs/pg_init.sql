/* Setup Airflow database */
CREATE USER airflow WITH LOGIN PASSWORD 'airflow';

CREATE DATABASE airflow_db WITH OWNER airflow;
REVOKE ALL PRIVILEGES ON DATABASE airflow_db FROM public;
GRANT ALL PRIVILEGES ON DATABASE airflow_db TO airflow;

/* Setup Backend database */
CREATE DATABASE backend WITH OWNER postgres;
