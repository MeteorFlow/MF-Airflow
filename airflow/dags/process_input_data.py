import logging
import pathlib

import pendulum

from airflow import DAG
from airflow.decorators import task
from airflow.exceptions import AirflowSkipException
from airflow.hooks.base import BaseHook
from airflow.models import Variable
from airflow.providers.sftp.hooks.sftp import SFTPHook
# from airflow.providers.sftp.operators.sftp import SFTPOperation, SFTPOperator

INPUT_FILE_PATH = "/sftp/test.txt"
LOCAL_TMP_PATH = "/Users/ducth/PycharmProjects/MeteorFlow/MF-Airflow/data/UF/NHB190513012007.RAW23DN"

with DAG(
    "process_input_data",
    start_date=pendulum.datetime(2023, 12, 27, tz="Asia/Ho_chi_minh"),
    schedule="*/1 * * * *",
) as dag:

    @task()
    def check_for_sftp_file():
        previous_processing_date: pendulum.datetime.DateTime = pendulum.parse(  # type: ignore
            Variable.get("sftp_prev_ts", None)
        )

        sftp_hook: SFTPHook = BaseHook.get_hook("sftp_conn")  # type: ignore

        file_mod_timestamp = sftp_hook.get_mod_time(INPUT_FILE_PATH)
        file_mod_time = pendulum.from_format(
            file_mod_timestamp, "YYYYMMDDHHmmss", tz="Asia/Ho_chi_minh"
        )

        if previous_processing_date and previous_processing_date >= file_mod_time:
            raise AirflowSkipException("SFTP file has not been modified")

        Variable.set("sftp_prev_ts", file_mod_time)

    # download_sftp_files = SFTPOperator(
    #     task_id="download_sftp_files",
    #     ssh_conn_id="ssh_conn",
    #     operation=SFTPOperation.GET,
    #     remote_filepath=INPUT_FILE_PATH,
    #     local_filepath=LOCAL_TMP_PATH,
    # )

    @task()
    def transform_input_file():
        import pyart
        from pyart.core import Radar

        logger = logging.getLogger(__name__)

        input_file: Radar = pyart.io.read_sigmet(LOCAL_TMP_PATH)
        logger.info(input_file.time)

    transform_input_file()

    # check_for_sftp_file() >> download_sftp_files


if __name__ == "__main__":
    file_path = pathlib.Path(__file__).parent
    dag.test(conn_file_path=str(file_path / "../connections.json"))
