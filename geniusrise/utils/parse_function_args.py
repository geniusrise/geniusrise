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

import ast
import json


def parse_args_kwargs(args_list):
    args = []
    kwargs = {}

    def convert(value):
        try:
            return ast.literal_eval(value.replace('"', "") if '"' in value else value)
        except Exception:
            try:
                return int(value.replace('"', ""))
            except ValueError:
                try:
                    return float(value.replace('"', ""))
                except ValueError:
                    try:
                        return json.loads(value)
                    except ValueError:
                        return value

    for item in args_list:
        if item[0] == "{":
            i = json.loads(item)
            kwargs = {**kwargs, **i}
        elif "=" in item:
            key, value = item.split("=", 1)
            kwargs[key] = convert(value)
        else:
            args.append(convert(item))

    return args, kwargs
