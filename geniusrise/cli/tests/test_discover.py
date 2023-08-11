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
