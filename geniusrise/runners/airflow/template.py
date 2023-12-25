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

dag_template = """
from datetime import timedelta
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.providers.docker.operators.docker import DockerOperator

default_args = {
    'owner': '{{ owner }}',
    'retries': {{ retries }},
    'retry_delay': timedelta(minutes={{ retry_delay_minutes }}),
}

with DAG(
    dag_id='{{ dag_id }}',
    default_args=default_args,
    description='{{ description }}',
    schedule_interval={{ schedule_interval }},
    start_date={{ start_date }},
    catchup={{ catchup }},
) as dag:

    t1 = DockerOperator(
        task_id='{{ task_id }}',
        image='{{ image }}',
        api_version='{{ api_version }}',
        command='{{ command }}',
        container_name='{{ container_name }}',
        cpus='{{ cpus }}',
        docker_url='{{ docker_url }}',
        environment={{ environment }},
        private_environment={{ private_environment }},
        network_mode='{{ network_mode }}',
        tls_hostname='{{ tls_hostname }}',
        tls_ca_cert='{{ tls_ca_cert }}',
        tls_client_cert='{{ tls_client_cert }}',
        tls_client_key='{{ tls_client_key }}',
        tls_ssl_version='{{ tls_ssl_version }}',
        tls_assert_hostname='{{ tls_assert_hostname }}',
        tls_verify='{{ tls_verify }}',
        mem_limit='{{ mem_limit }}',
        user='{{ user }}',
        ports={{ ports }},
        volumes={{ volumes }},
        working_dir='{{ working_dir }}',
        xcom_push={{ xcom_push }},
        xcom_all={{ xcom_all }},
        auto_remove={{ auto_remove }},
        shm_size='{{ shm_size }}',
        tty={{ tty }},
        privileged={{ privileged }},
        cap_add={{ cap_add }},
        extra_hosts={{ extra_hosts }},
        tmp_dir='{{ tmp_dir }}',
        host_tmp_dir='{{ host_tmp_dir }}',
        dns={{ dns }},
        dns_search={{ dns_search }},
        mount_tmp_dir={{ mount_tmp_dir }},
        mount_volume={{ mount_volume }},
    )
"""
