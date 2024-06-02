import pendulum

from airflow import DAG
from airflow.decorators import task


__version__ = "0.0.1"

CONN_ID = "nha_be_s3"
BUCKET = "nha-be-processed"

with DAG(
    dag_id="median_filtering",
    schedule=None,
    start_date=pendulum.datetime(2010, 1, 1),
) as dag:

    @task
    def apply_median_filtering(**context):
        from airflow.providers.amazon.aws.hooks.s3 import S3Hook
        import re
        import logging

        import io
        import numpy

        logical_date: pendulum.DateTime = context["logical_date"].in_tz("Asia/Ho_Chi_Minh")
        expected_file_name_prefix = logical_date.format("[reflectivity]/YYYYMMDD")
        file_template = re.compile(r"reflectivity/(\d{8})T(\d{6})Z")

        logger = logging.getLogger("__name__")
        logger.info(expected_file_name_prefix)

        s3_hook = S3Hook(CONN_ID)
        received_files = s3_hook.list_keys(prefix=expected_file_name_prefix, bucket_name=BUCKET)
        for file_name in received_files:
            logger.info("Processing file: %s", file_name)
            file_name_matches = file_template.match(file_name)
            logger.info(file_name_matches)
            assert file_name_matches is not None

            s3_client = s3_hook.get_conn()

            reflectivity_byte_stream = io.BytesIO()
            s3_client.download_fileobj(
                Key=file_name, Bucket=BUCKET, Fileobj=reflectivity_byte_stream
            )

            reflectivity_byte_stream.seek(0)
            reflectivity: numpy.ndarray = numpy.load(reflectivity_byte_stream)

            # Define the size of the neighborhood (3x3 window)
            neighborhood_size = 3
            offset = neighborhood_size // 2

            memory_buffer = numpy.zeros_like(reflectivity)

            for i in range(offset, reflectivity.shape[0] - offset):
                for j in range(offset, reflectivity.shape[1] - offset):
                    neighborhood = reflectivity[
                        i - offset : i + offset + 1,
                        j - offset : j + offset + 1,
                    ]
                    median_value = numpy.median(neighborhood)
                    memory_buffer[i, j] = median_value

            # Reset stream to write
            output_stream = io.BytesIO()
            numpy.save(output_stream, memory_buffer)
            output_stream.seek(0)
            s3_client.upload_fileobj(
                Fileobj=output_stream,
                Key=f"reflectivity-median-filtering/{logical_date.format('YYYYMMDD')}T{file_name_matches.group(2)}Z",
                Bucket=BUCKET,
            )

    apply_median_filtering()


if __name__ == "__main__":
    dag.test(execution_date=pendulum.datetime(2019, 5, 10, tz="Asia/Ho_Chi_Minh"))
