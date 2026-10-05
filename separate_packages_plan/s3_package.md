# geniusrise-data-s3 Package

## Directory Structure

```
geniusrise-data-s3/
  geniusrise_data_s3/
    __init__.py
    batch_input.py
    batch_output.py
  setup.py
  README.md
  requirements.txt
```

## Implementation

### setup.py

```python
from setuptools import setup, find_packages

setup(
    name="geniusrise-data-s3",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "geniusrise>=0.2.0",
        "boto3>=1.34.0",
    ],
    entry_points={
        "geniusrise.plugins.input": [
            "batch=geniusrise_data_s3:register_input_plugin",
        ],
        "geniusrise.plugins.output": [
            "batch=geniusrise_data_s3:register_output_plugin",
        ],
    },
    author="Geniusrise",
    author_email="ixaxaar@geniusrise.ai",
    description="S3 batch data handling for Geniusrise",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/geniusrise/geniusrise-data-s3",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
)
```

### requirements.txt

```
geniusrise>=0.2.0
boto3>=1.34.0
```

### README.md

````markdown
# Geniusrise S3 Data Backend

This package provides S3 batch data handling capabilities for the Geniusrise
framework.

## Installation

```bash
pip install geniusrise-data-s3
```
````

## Usage

Once installed, the S3 batch data backends will be automatically available in
your Geniusrise application:

```python
from geniusrise import Task
from geniusrise.core.data import INPUT_BACKENDS, OUTPUT_BACKENDS

# Check if batch backends are available
if "batch" in INPUT_BACKENDS and "batch" in OUTPUT_BACKENDS:
    # Create a task with batch input/output
    task = Task.create(
        some_task_class,
        input_type="batch",
        input_folder="/tmp/input",
        input_s3_bucket="my-bucket",
        input_s3_folder="input-data",
        output_type="batch",
        output_folder="/tmp/output",
        output_s3_bucket="my-bucket",
        output_s3_folder="output-data"
    )
```

Or in YAML configuration:

```yaml
version: '1'

tasks:
  my_task:
    name: SomeTask
    input:
      type: batch
      args:
        input_folder: /tmp/input
        input_s3_bucket: my-bucket
        input_s3_folder: input-data
    output:
      type: batch
      args:
        output_folder: /tmp/output
        output_s3_bucket: my-bucket
        output_s3_folder: output-data
    # ... other configuration
```

## Configuration

The batch data backends support the following configuration options:

### BatchInput

- `input_folder`: Local folder for input data
- `input_s3_bucket`: S3 bucket for input data
- `input_s3_folder`: S3 folder prefix for input data
- `partition_scheme`: Optional partitioning scheme for S3 data

### BatchOutput

- `output_folder`: Local folder for output data
- `output_s3_bucket`: S3 bucket for output data
- `output_s3_folder`: S3 folder prefix for output data
- `partition_scheme`: Optional partitioning scheme for S3 data

````

### geniusrise_data_s3/__init__.py

```python
# 🧠 Geniusrise
# Copyright (C) 2023-2025  geniusrise.ai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from geniusrise_data_s3.batch_input import BatchInput
from geniusrise_data_s3.batch_output import BatchOutput

__version__ = "0.1.0"
__all__ = ["BatchInput", "BatchOutput", "register_input_plugin", "register_output_plugin"]

def register_input_plugin():
    """
    Register input plugin with the Geniusrise framework.
    This function is called by the plugin discovery system.
    """
    try:
        from geniusrise.core.data import register_input_backend
        register_input_backend("batch", BatchInput)
        return {"batch": BatchInput}
    except ImportError:
        # This might happen during setup or if geniusrise is not installed
        return {}

def register_output_plugin():
    """
    Register output plugin with the Geniusrise framework.
    This function is called by the plugin discovery system.
    """
    try:
        from geniusrise.core.data import register_output_backend
        register_output_backend("batch", BatchOutput)
        return {"batch": BatchOutput}
    except ImportError:
        # This might happen during setup or if geniusrise is not installed
        return {}
````

### geniusrise_data_s3/batch_input.py

````python
# 🧠 Geniusrise
# Copyright (C) 2023-2025  geniusrise.ai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil
import time
from typing import Dict, Optional, Union

import boto3

from geniusrise.core.data import Input


class FileNotExistError(Exception):
    """❌ Custom exception for file not existing."""


class BatchInput(Input):
    r"""
    📁 BatchInput: Manages batch input data.

    Attributes:
        input_folder (str): Folder to read input files.
        bucket (str): S3 bucket name.
        s3_folder (str): Folder within the S3 bucket.
        partition_scheme (Optional[str]): Partitioning scheme for S3, e.g., "year/month/day".

    Raises:
        FileNotExistError: If the file does not exist.

    Args:
        input_folder (str): Folder to read input files from.
        bucket (str): S3 bucket name.
        s3_folder (str): Folder within the S3 bucket.
        partition_scheme (Optional[str]): Partitioning scheme for S3, e.g., "year/month/day".

    Usage:

        # Initialize BatchInput
        ```python
        input = BatchInput("/path/to/input", "my_bucket", "s3/folder")
        ```

        ### Get the input folder
        ```python
        folder = input.get()
        ```

        ### Compose multiple BatchInput instances
        ```python
        composed = input.compose(input1, input2)
        ```

        ### Copy files from S3 to the input folder
        ```python
        input.from_s3()
        ```

        # Collect metrics
        ```python
        metrics = input.collect_metrics()
        ```
    """

    def __init__(
        self,
        input_folder: str,
        bucket: str,
        s3_folder: str,
        partition_scheme: Optional[str] = None,
    ) -> None:
        """Initialize a new BatchInput instance."""
        super().__init__()
        self.input_folder = input_folder
        self.bucket = bucket
        self.s3_folder = s3_folder
        self.partition_scheme = partition_scheme
        self._metrics: Dict[str, float] = {}

    def get(self) -> str:
        """
        Get the input folder path.

        Returns:
            str: The path to the input folder.
        """
        return self.input_folder

    def from_s3(
        self,
        bucket: Optional[str] = None,
        s3_folder: Optional[str] = None,
    ) -> None:
        """
        Copy contents from a given S3 bucket and location to the input folder.

        Raises:
            Exception: If the input folder is not specified.
        """
        self.bucket = bucket if bucket else self.bucket

        if not self.bucket or self.bucket == "None":
            self.log.warn("S3 Bucket is None, not fetching.")
            return

        self.s3_folder = s3_folder if s3_folder else self.s3_folder

        start_time = time.time()
        if self.input_folder:
            s3 = boto3.resource("s3")
            _bucket = s3.Bucket(self.bucket)
            prefix = self._get_partitioned_key(self.s3_folder)
            for obj in _bucket.objects.filter(Prefix=prefix):
                if not os.path.exists(os.path.dirname(f"{self.input_folder}/{obj.key}")):
                    os.makedirs(os.path.dirname(f"{self.input_folder}/{obj.key}"))
                _bucket.download_file(obj.key, f"{self.input_folder}/{obj.key}")
            end_time = time.time()
            self._metrics["from_s3_time"] = end_time - start_time
        else:
            raise Exception("❌ Input folder not specified.")

    def compose(self, *inputs: "Input") -> Union[bool, str]:
        """
        Compose multiple BatchInput instances by merging their input folders.

        Args:
            inputs (Input): Variable number of BatchInput instances.

        Returns:
            Union[bool, str]: True if successful, error message otherwise.
        """
        try:
            for input_instance in inputs:
                if not isinstance(input_instance, BatchInput):
                    return f"❌ Incompatible input type: {type(input_instance).__name__}"

                src_folder = input_instance.get()
                for filename in os.listdir(src_folder):
                    src_path = os.path.join(src_folder, filename)
                    dest_path = os.path.join(self.input_folder, filename)

                    if os.path.isfile(src_path):
                        shutil.copy2(src_path, dest_path)

            return True
        except Exception as e:
            self.log.exception(f"❌ Error during composition: {e}")
            return str(e)

    def collect_metrics(self) -> Dict[str, float]:
        """
        Collect and return metrics, then clear them for future collection.

        Returns:
            Dict[str, float]: Dictionary containing metrics.
        """
        collected_metrics = self._metrics.copy()
        self._metrics.clear()
        return collected_metrics

    def _get_partitioned_key(self, prefix: str) -> str:
        """
        Generate a partitioned S3 key based on the partitioning scheme.

        Args:
            prefix (str): The s3 folder prefix to use

        Returns:
            str: The partitioned S3 key.
        """
        if self.partition_scheme:
            partitioned_key = time.strftime(self.partition_scheme)
            return f"{prefix}/{partitioned_key}"
        else:
            return self.s3_folder
````

### geniusrise_data_s3/batch_output.py

````python
# 🧠 Geniusrise
# Copyright (C) 2023-2025  geniusrise.ai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import shutil
import time
from typing import Any, Dict, Optional, Union

import boto3

from geniusrise.core.data import Output


class BatchOutput(Output):
    r"""
    📁 BatchOutput: Manages batch output data.

    Attributes:
        output_folder (str): Folder to write output files.
        bucket (str): S3 bucket name.
        s3_folder (str): Folder within the S3 bucket.
        partition_scheme (Optional[str]): Partitioning scheme for S3, e.g., "year/month/day".

    Args:
        output_folder (str): Folder to write output files.
        bucket (str): S3 bucket name.
        s3_folder (str): Folder within the S3 bucket.
        partition_scheme (Optional[str]): Partitioning scheme for S3, e.g., "year/month/day".

    Usage:

        # Initialize BatchOutput
        ```python
        output = BatchOutput("/path/to/output", "my_bucket", "s3/folder")
        ```

        ### Save data to a file
        ```python
        output.save({"key": "value"}, "data.json")
        ```

        ### Compose multiple BatchOutput instances
        ```python
        composed = output.compose(output1, output2)
        ```

        ### Copy files from the output folder to S3
        ```python
        output.to_s3()
        ```

        ### Collect metrics
        ```python
        metrics = output.collect_metrics()
        ```
    """

    def __init__(
        self,
        output_folder: str,
        bucket: str,
        s3_folder: str,
        partition_scheme: Optional[str] = None,
    ) -> None:
        """Initialize a new BatchOutput instance."""
        super().__init__()
        self.output_folder = output_folder
        self.bucket = bucket
        self.s3_folder = s3_folder
        self.partition_scheme = partition_scheme
        self._metrics: Dict[str, float] = {}

    def save(self, data: Any, filename: str) -> None:
        """
        Save data to a file.

        Args:
            data (Any): The data to save.
            filename (str): The name of the file to save the data to.

        Raises:
            Exception: If an error occurs while saving the data.
        """
        try:
            # Ensure output folder exists
            os.makedirs(self.output_folder, exist_ok=True)

            # Prepare the file path
            file_path = os.path.join(self.output_folder, filename)

            # Ensure directory structure exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Save the data
            with open(file_path, "w") as f:
                if isinstance(data, str):
                    f.write(data)
                else:
                    json.dump(data, f, indent=2)

            self.log.debug(f"✅ Saved data to {file_path}")
        except Exception as e:
            self.log.exception(f"❌ Failed to save data to {filename}: {e}")
            raise

    def to_s3(
        self,
        bucket: Optional[str] = None,
        s3_folder: Optional[str] = None,
    ) -> None:
        """
        Copy contents from the output folder to a given S3 bucket and location.

        Args:
            bucket (Optional[str]): The S3 bucket to upload to. If None, uses the instance's bucket.
            s3_folder (Optional[str]): The S3 folder to upload to. If None, uses the instance's s3_folder.

        Raises:
            Exception: If the output folder is not specified or doesn't exist.
        """
        self.bucket = bucket if bucket else self.bucket

        if not self.bucket or self.bucket == "None":
            self.log.warn("S3 Bucket is None, not uploading.")
            return

        self.s3_folder = s3_folder if s3_folder else self.s3_folder

        start_time = time.time()
        if self.output_folder and os.path.exists(self.output_folder):
            s3 = boto3.resource("s3")
            _bucket = s3.Bucket(self.bucket)
            prefix = self._get_partitioned_key(self.s3_folder)

            # Upload all files in the output folder to S3
            for root, _, files in os.walk(self.output_folder):
                for file in files:
                    local_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_path, self.output_folder)
                    s3_key = f"{prefix}/{relative_path}"
                    _bucket.upload_file(local_path, s3_key)
                    self.log.debug(f"✅ Uploaded {local_path} to s3://{self.bucket}/{s3_key}")

            end_time = time.time()
            self._metrics["to_s3_time"] = end_time - start_time
        else:
            raise Exception("❌ Output folder not specified or doesn't exist.")

    def compose(self, *outputs: "Output") -> Union[bool, str]:
        """
        Compose multiple BatchOutput instances by merging their output folders.

        Args:
            outputs (Output): Variable number of BatchOutput instances.

        Returns:
            Union[bool, str]: True if successful, error message otherwise.
        """
        try:
            for output_instance in outputs:
                if not isinstance(output_instance, BatchOutput):
                    return f"❌ Incompatible output type: {type(output_instance).__name__}"

                src_folder = output_instance.output_folder
                for root, _, files in os.walk(src_folder):
                    for file in files:
                        src_path = os.path.join(root, file)
                        relative_path = os.path.relpath(src_path, src_folder)
                        dest_path = os.path.join(self.output_folder, relative_path)

                        # Ensure destination directory exists
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                        # Copy the file
                        shutil.copy2(src_path, dest_path)

            return True
        except Exception as e:
            self.log.exception(f"❌ Error during composition: {e}")
            return str(e)

    def flush(self) -> None:
        """
        Flush the output by copying it to S3.
        """
        self.to_s3()

    def collect_metrics(self) -> Dict[str, float]:
        """
        Collect and return metrics, then clear them for future collection.

        Returns:
            Dict[str, float]: Dictionary containing metrics.
        """
        collected_metrics = self._metrics.copy()
        self._metrics.clear()
        return collected_metrics

    def _get_partitioned_key(self, prefix: str) -> str:
        """
        Generate a partitioned S3 key based on the partitioning scheme.

        Args:
            prefix (str): The s3 folder prefix to use

        Returns:
            str: The partitioned S3 key.
        """
        if self.partition_scheme:
            partitioned_key = time.strftime(self.partition_scheme)
            return f"{prefix}/{partitioned_key}"
        else:
            return prefix
````
