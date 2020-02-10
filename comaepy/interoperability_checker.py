#!/usr/bin/env python

"""
This script checks that two archives containing JSON files follow the same
structure.
"""

import json
import os
import pandas as pd
import sys
import zipfile as zip

class MissingKey(Exception):
    def __init__(self, jsonpath):
        self.jsonpath = jsonpath

class JSONArchivePath:
    def __init__(self, filename, jsonpath):
        self.filename = filename
        self.jsonpath = jsonpath

class JSONArchive:
    def __init__(self, archive_path):
        self.zf = zip.ZipFile(archive_path, "r")
        self.json_objects = {}

    def __del__(self):
        self.zf.close()

    def getFiles(self):
        return [ f.filename for f in self.zf.infolist() if not f.is_dir() ]

    def getJSON(self, name):
        if name in self.json_objects.keys():
            return self.json_objects[name]

        path = self.zf.extract(name)
        with open(path, "r", encoding="latin-1") as f:
            obj = json.loads(f.read())
            self.json_objects[name] = obj
            return obj

    def getSubJSON(self, name, jsonpath):
        obj = self.getJSON(name)
        sub = obj
        for key in jsonpath:
            if key in sub.keys():
                sub = sub[key]
            else:
                raise MissingKey(jsonpath)
        return sub


def diff_json_objects(old, new):
    state = {
        "problems": pd.DataFrame(columns = ["jsonpath", "problem", "hint"])
    }

    def helper(state, jsonpath, old_obj, new_obj):
        if type(old_obj) is dict:
            if type(new_obj) is not dict:
                state["problems"] = state["problems"].append([{
                    "jsonpath": jsonpath,
                    "problem": "Wrong type, should be object",
                    "hint": type(new_obj),
                    "old_length": len(json.dumps(old_obj)),
                    "new_length": len(json.dumps(new_obj)),
                }], sort=False)

            else:
                # Recurse on each key. If one is missing, add an error.
                for key in old_obj.keys():
                    if key in new_obj.keys():
                        helper(state, jsonpath + [key], old_obj[key], new_obj[key])
                    else:
                        state["problems"] = state["problems"].append([{
                            "jsonpath": jsonpath + [key],
                            "problem": "Missing key",
                            "old_length": len(json.dumps(old_obj)),
                            "new_length": len(json.dumps(new_obj)),
                        }], sort=False)

        elif type(old_obj) is list:
            if type(new_obj) is not list:
                state["problems"] = state["problems"].append([{
                    "jsonpath": jsonpath,
                    "problem": "Wrong type, should be array",
                    "hint": type(new_obj),
                    "old_length": len(json.dumps(old_obj)),
                    "new_length": len(json.dumps(new_obj)),
                }], sort=False)

            elif len(old_obj) > 0 and len(new_obj) > 0:
                helper(state, jsonpath + ["[]"], old_obj[0], new_obj[0])

        else:
            if type(new_obj) != type(old_obj) and type(new_obj) is not None and type(old_obj) is not None:
                state["problems"] = state["problems"].append([{
                    "jsonpath": jsonpath,
                    "problem": "Incompatible types",
                    "hint": "%s vs %s" % (type(new_obj), type(old_obj)),
                    "old_length": len(json.dumps(old_obj)),
                    "new_length": len(json.dumps(new_obj)),
                }], sort=False)

    helper(state, [], old, new)
    return state["problems"]

def diff_archives(old_archive, new_archive):
    problems = pd.DataFrame(
        columns = ["filename", "jsonpath", "problem", "hint", "old_length", "new_length"]
    )

    for filename in old_archive.getFiles():
        print("Diffing %s..." % filename)

        old_obj = old_archive.getJSON(filename)

        # Check the fields .processObject.processId are equal if present.
        try:
            assert(old_obj["processObject"]["processId"] == new_obj["processObject"]["processId"])
        except:
            # Ignore, it will be caught in the CSV
            ()

        # Recursively compare the JSON structure or add an error if the file is
        # missing in the new archive.
        try:
            new_obj = new_archive.getJSON(filename)

            new_problems = diff_json_objects(old_obj, new_obj)
            new_problems["filename"] = filename
            problems = problems.append(new_problems, sort=False)

        except KeyError:
            problems = problems.append([{
                "filename": filename,
                "problem": "Missing file",
            }], sort=False)

    return problems

if len(sys.argv) != 3:
    print("Usage: %s PATH_TO_OLD_ARCHIVE PATH_TO_NEW_ARCHIVE")
    sys.exit(1)

old_archive = JSONArchive(sys.argv[1])
new_archive = JSONArchive(sys.argv[2])

problems = diff_archives(old_archive, new_archive)
problems["jsonpath"] = problems["jsonpath"].apply(
    lambda keys: ".".join(keys) if type(keys) is list else keys
)
problems.to_csv("result.csv", index=False)