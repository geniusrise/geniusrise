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

from typing import Any, Dict

import yaml


class AirflowCodeGenerator:
    """
    Class to generate Python code for Airflow DAGs based on a YAML configuration.
    """

    def __init__(self, yaml_file_path: str):
        """
        Initialize the code generator with the path to the YAML file.

        Args:
            yaml_file_path (str): Path to the YAML file.
        """
        self.yaml_file_path = yaml_file_path

    def _generate_operator_code(self, name: str, operator_type: str, method: str, args: Dict[str, Any]) -> str:
        """
        Generate Python code for an Airflow operator.

        Args:
            name (str): Name of the operator.
            operator_type (str): Type of the operator (Spout or Bolt).
            method (str): Method to be called in the operator.
            args (Dict[str, Any]): Arguments to be passed to the method.

        Returns:
            str: Generated Python code for the operator.
        """
        args_str = ", ".join([f"{key}={repr(value)}" for key, value in args.items()])
        return f"""
class {name}(BaseOperator):
    def execute(self, context):
        self.log.info("Executing {operator_type} {name}")
        instance = {operator_type}(method="{method}", {args_str})
        instance.{method}()
"""

    def generate_airflow_code(self) -> str:
        """
        Generate Python code for Airflow DAG based on YAML configuration.

        Returns:
            str: Generated Python code for the Airflow DAG.
        """
        with open(self.yaml_file_path, "r") as f:
            yaml_data = yaml.safe_load(f)

        code_blocks = []
        for spout_name, spout_data in yaml_data.get("spouts", {}).items():
            code_blocks.append(
                self._generate_operator_code(spout_name, "Spout", spout_data["method"], spout_data["args"])
            )

        for bolt_name, bolt_data in yaml_data.get("bolts", {}).items():
            code_blocks.append(self._generate_operator_code(bolt_name, "Bolt", bolt_data["method"], bolt_data["args"]))

        return "\n".join(code_blocks)


if __name__ == "__main__":
    # Initialize the code generator with the path to the YAML file
    code_generator = AirflowCodeGenerator("your_file.yaml")

    # Generate Python code for Airflow DAG
    airflow_code = code_generator.generate_airflow_code()

    # Write the generated code to a Python file
    with open("generated_airflow_dag.py", "w") as f:
        f.write(airflow_code)
