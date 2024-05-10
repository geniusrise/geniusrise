# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
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

# import pytest
# from geniusrise.cli.discover import Discover, DiscoveredSpout


# # Mocking an installed extension
# @pytest.fixture
# def mock_installed_extension(monkeypatch):
#     class MockEntryPoint:
#         name = "mock_extension"

#         def load(self):
#             class MockSpout:
#                 def __init__(self, arg1, arg2="default"):
#                     pass

#             return MockSpout

#     monkeypatch.setattr("pkg_resources.iter_entry_points", lambda group: [MockEntryPoint()])


# # Mocking a user-defined spout in a directory
# @pytest.fixture
# def mock_directory(tmpdir):
#     p = tmpdir.mkdir("sub").join("my_spout.py")
#     p.write(
#         """
# from geniusrise import Spout

# class MySpout(Spout):
#     def whatever_lol(self, x, y=42):
#         self.save(x+y)
#     """
#     )
#     return tmpdir


# def test_discover_installed_extensions(mock_installed_extension):
#     discover = Discover()
#     classes = discover.scan_directory()
#     assert "MockSpout" in classes
#     assert isinstance(classes["MockSpout"], DiscoveredSpout)
#     assert classes["MockSpout"].init_args == {"arg1": "No type hint provided 😢", "arg2": str}


# def test_discover_user_defined_spouts(mock_directory):
#     discover = Discover(directory=str(mock_directory))
#     classes = discover.scan_directory()
#     assert "MySpout" in classes
#     assert isinstance(classes["MySpout"], DiscoveredSpout)
#     assert classes["MySpout"].init_args == {"x": "No type hint provided 😢", "y": int}
