import pendulum

from airflow import DAG
from airflow.decorators import task


__version__ = "0.0.1"

CONN_ID = "nha_be_s3"
SOURCE_BUCKET = "nha-be-radar"
DEST_BUCKET = "nha-be-processed"

with DAG(
    dag_id="nha_be_processed_data",
    schedule="@daily",
    start_date=pendulum.datetime(2019, 1, 1),
) as dag:

    @task.short_circuit()
    def check_raw_file_exist(**context):
        from airflow.providers.amazon.aws.hooks.s3 import S3Hook
        import logging

        logical_date: pendulum.DateTime = context["logical_date"].in_tz("Asia/Ho_Chi_Minh")
        expected_file_name_prefix = f"NHB{logical_date.format('YYMMDD')}"
        logging.info(expected_file_name_prefix)

        s3_hook = S3Hook(CONN_ID)
        received_files = s3_hook.list_keys(
            prefix=expected_file_name_prefix, bucket_name=SOURCE_BUCKET, max_items=1
        )

        logging.info("%s", received_files)

        return len(received_files)

    @task()
    def copy_to_s3(**context):
        from airflow.providers.amazon.aws.hooks.s3 import S3Hook
        import re
        import logging

        import io
        import tempfile
        import pyart
        import numpy

        logical_date: pendulum.DateTime = context["logical_date"].in_tz("Asia/Ho_Chi_Minh")
        expected_file_name_prefix = f"NHB{logical_date.format('YYMMDD')}"

        s3_hook = S3Hook(CONN_ID)
        received_files = s3_hook.list_keys(
            prefix=expected_file_name_prefix, bucket_name=SOURCE_BUCKET
        )

        file_template = re.compile(r"NHB(\d{6})(\d{6})\.(\w{7})")

        logger = logging.getLogger("__name__")

        for file_name in received_files:
            logger.info("Processing file: %s", file_name)
            file_name_matches = file_template.match(file_name)

            if not file_name_matches:
                logging.warning("File name does not match convention, skipped")
                continue

            with tempfile.NamedTemporaryFile() as temp_file:
                s3_client = s3_hook.get_conn()

                s3_client.download_fileobj(Key=file_name, Bucket=SOURCE_BUCKET, Fileobj=temp_file)
                radar_content = pyart.io.read_sigmet(temp_file.name)

                reflectivity_byte_stream = io.BytesIO()
                numpy.save(reflectivity_byte_stream, radar_content.fields["reflectivity"]["data"])

                # Reset stream to write
                reflectivity_byte_stream.seek(0)
                s3_client.upload_fileobj(
                    Fileobj=reflectivity_byte_stream,
                    Key=f"reflectivity/{logical_date.format('YYYYMMDD')}T{file_name_matches.group(2)}Z",
                    Bucket=DEST_BUCKET,
                )

            s3_hook.copy_object(
                source_bucket_key=file_name,
                source_bucket_name=SOURCE_BUCKET,
                dest_bucket_key=f"{logical_date.format('YYYYMMDD')}T{file_name_matches.group(2)}Z",
                dest_bucket_name=DEST_BUCKET,
            )

        s3_hook.delete_objects(bucket=SOURCE_BUCKET, keys=received_files)

    check_raw_file_exist() >> copy_to_s3()


if __name__ == "__main__":
    dag.test(execution_date=pendulum.datetime(2019, 5, 11, tz="Asia/Ho_Chi_Minh"))
