#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

install_python_dependencies() {
  pip install --upgrade pip
  pip install -r requirements.txt -r requirements.dev.txt
}

install_python_dependencies

# Start local PostgreSQL database
docker compose up -d

# Airflow init
airflow db migrate
bash -c "$script_dir"/create-admin-user.sh