# Mobile Verification Toolkit (MVT)
# Copyright (c) 2021-2022 Claudio Guarnieri.
# Use of this software is governed by the MVT License 1.1 that can be found at
#   https://license.mvt.re/1.1/

import datetime
import os

from mvt.common.utils import convert_timestamp_to_iso

from ..base import IOSExtraction


class Filesystem(IOSExtraction):
    """This module extracts creation and modification date of files from a
    full file-system dump.


    """

    def __init__(self, file_path=None, base_folder=None, output_folder=None,
                 fast_mode=False, log=None, results=[]):
        super().__init__(file_path=file_path, base_folder=base_folder,
                         output_folder=output_folder, fast_mode=fast_mode,
                         log=log, results=results)

    def serialize(self, record):
        return {
            "timestamp": record["modified"],
            "module": self.__class__.__name__,
            "event": "entry_modified",
            "data": record["path"],
        }

    def check_indicators(self):
        if not self.indicators:
            return

        for result in self.results:
            if "path" not in result:
                continue

            ioc = self.indicators.check_file_path(result["path"])
            if ioc:
                result["matched_indicator"] = ioc
                self.detected.append(result)

            # If we are instructed to run fast, we skip the rest.
            if self.fast_mode:
                continue

            for ioc in self.indicators.get_iocs("processes"):
                parts = result["path"].split("/")
                if ioc["value"] in parts:
                    self.log.warning("Found known suspicious process name mentioned in file at path \"%s\" matching indicators from \"%s\"",
                                     result["path"], ioc["name"])
                    result["matched_indicator"] = ioc
                    self.detected.append(result)

    def run(self):
        for root, dirs, files in os.walk(self.base_folder):
            for dir_name in dirs:
                try:
                    dir_path = os.path.join(root, dir_name)
                    result = {
                        "path": os.path.relpath(dir_path, self.base_folder),
                        "modified": convert_timestamp_to_iso(datetime.datetime.utcfromtimestamp(os.stat(dir_path).st_mtime)),
                    }
                except Exception:
                    continue
                else:
                    self.results.append(result)

            for file_name in files:
                try:
                    file_path = os.path.join(root, file_name)
                    result = {
                        "path": os.path.relpath(file_path, self.base_folder),
                        "modified": convert_timestamp_to_iso(datetime.datetime.utcfromtimestamp(os.stat(file_path).st_mtime)),
                    }
                except Exception:
                    continue
                else:
                    self.results.append(result)
