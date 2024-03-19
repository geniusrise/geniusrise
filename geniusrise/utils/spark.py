# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess
from typing import List, Optional, Dict

from geniusrise.logging import setup_logger

log = setup_logger()


def read_requirements(requirements_path: str = "requirements.txt") -> List[str]:
    """
    Reads the package dependencies from a requirements.txt file.

    Args:
        requirements_path (str): Path to the requirements.txt file.

    Returns:
        List[str]: List of package dependencies.
    """
    try:
        with open(requirements_path, "r") as file:
            packages = [line.strip() for line in file.readlines() if line.strip() and not line.startswith("#")]
        return packages
    except FileNotFoundError:
        log.info(f"🚫 File {requirements_path} not found.")
        return []


def package_and_submit_spark_job(
    app_name: str,
    entry_script: str,
    master_url: str = "local[*]",
    requirements_path: Optional[str] = "requirements.txt",
    additional_requirements: Optional[List[str]] = None,
    py_files: Optional[List[str]] = None,
    spark_conf: Optional[Dict[str, str]] = None,
) -> None:
    """
    Packages and submits a PySpark job to a Spark cluster, automatically including package dependencies from requirements.txt.

    Args:
        app_name (str): Name of the Spark application.
        entry_script (str): The entry point script for the Spark job.
        master_url (str): URL of the Spark master (default is local mode).
        requirements_path (Optional[str]): Path to the requirements.txt file for additional PyPi packages.
        additional_requirements (Optional[List[str]]): List of additional python package requirements.
        py_files (Optional[List[str]]): List of additional Python files to include.
        spark_conf (Optional[Dict[str, str]]): Dictionary of Spark configuration options.
    """
    # Include additional packages from requirements.txt if specified
    packages = read_requirements(requirements_path) + (additional_requirements if additional_requirements else [])
    packages = list(filter(None, packages))  # Remove any None values

    # Construct the spark-submit command
    submit_cmd = ["spark-submit", "--name", app_name, "--master", master_url]

    if packages:
        submit_cmd.append("--packages")
        submit_cmd.append(",".join(packages))

    if py_files:
        submit_cmd.append("--py-files")
        submit_cmd.append(",".join(py_files))

    if spark_conf:
        for key, value in spark_conf.items():
            submit_cmd.append(f"--conf {key}={value}")

    submit_cmd.append(entry_script)

    # Log the submission command
    log.info("🚀 Submitting Spark job with command:")
    log.info("__________________________________________________________")
    log.info(" ".join(submit_cmd))
    log.info("__________________________________________________________")

    # Execute the spark-submit command
    process = subprocess.Popen(submit_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode == 0:
        log.info("✅ Spark job submitted successfully.")
        log.info(stdout.decode("utf-8"))
    else:
        log.info("❌ Error submitting Spark job.")
        log.info(stderr.decode("utf-8"))
