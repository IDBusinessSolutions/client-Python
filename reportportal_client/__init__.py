"""
Copyright (c) 2018 http://reportportal.io .

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from .service import ReportPortalService
from time import time

__all__ = ('ReportPortalService',)


POST_LOGBATCH_RETRY_COUNT = 10

endpoint = "http://report-portal.idbs-dev.com"
project = "tara_integration"
# You can get UUID from user profile page in the Report Portal.
token = "42c4195e-ecea-44f7-af51-09e861516863"
launch_name = "RF Test launch"
launch_doc = "Testing RF tests."
launch_time = str(int(time() * 1000))


class reportportal_client:

    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self):
        self.rp_service = ReportPortalService(endpoint, project, token)
        self.rp_service.start_launch(launch_name, launch_time, launch_doc)
        self.test_id = None
        self.suite_id = None


    def start_suite(self, name, attributes):
        self.suite_id = self.rp_service.start_test_item(name, self.now(), "SUITE")


    def end_suite(self, name, attributes):
        status = self.attribute_status(attributes["status"])
        self.rp_service.finish_test_item(self.suite_id, self.now(), status)


    def start_test(self, name, attributes):
        self.test_id = self.rp_service.start_test_item(name, self.now(), "TEST")


    def end_test(self, name, attributes):
        status = self.attribute_status(attributes["status"])
        self.rp_service.finish_test_item(self.test_id, self.now(), status)


    def now(self):
        time_now = str(int(time() * 1000))

        return time_now


    def attribute_status(self, status):
        if status == "PASS":
            rp_status = "PASSED"
        else:
            rp_status = "FAILED"

        return rp_status


    def close(self):
        self.rp_service.finish_launch(self.now())
