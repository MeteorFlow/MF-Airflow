#!/usr/bin/env bash
#: Your comments here.

set -o errexit
set -o nounset
set -o pipefail

trap clean_up ERR EXIT SIGINT SIGTERM

clean_up() {
    trap - ERR EXIT SIGINT SIGTERM
    # Remove temporary files/directories, log files or rollback changes.
}

airflow users create \
    --username admin \
    --firstname Admin \
    --lastname admin \
    --role Admin \
    --email admin@example.org \
    --password admin

exit 0
