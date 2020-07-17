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

        # Not sure what this is for
        self.test_id = None
        self.suite_id = None

        # List for scenario info
        self.scenario_info = []


    def start_suite(self, name, attributes):

        # standardise suite name
        name = self.standardise_string(name)

        # standardise suite and test names
        for index, value in enumerate(attributes['suites']):
            attributes['suites'][index] = self.standardise_string(value)

        # standardise test names
        for index, value in enumerate(attributes['tests']):
            attributes['tests'][index] = self.standardise_string(value)

        # Create dict of suite properties
        suite_data = {}
        suite_data['name'] = name
        suite_data['child_suites'] = attributes['suites']
        suite_data['tests'] = attributes['tests']
        suite_data['parent_rp_id'] = self.find_parent_suite_for_suite(name)

        # start Report Portal Item (returns report portal item ID)
        suite_data['rp_id'] = self.rp_service.start_test_item(name, self.now(), "SUITE", parent_item_id=suite_data['parent_rp_id'])

        # Append suite properties dict to suite info
        self.scenario_info.append(suite_data)


    def end_suite(self, name, attributes):
        status = self.attribute_status(attributes["status"])
        self.rp_service.finish_test_item(self.suite_id, self.now(), status)


    def start_test(self, name, attributes):

        # standardise test name
        name = self.standardise_string(name)

        # Check for Parent item ID
        parent = self.find_parent_suite_for_test(name)

        # Start test item
        self.test_id = self.rp_service.start_test_item(name, self.now(), "TEST", parent_item_id=parent)


    def end_test(self, name, attributes):
        status = self.attribute_status(attributes["status"])
        self.rp_service.finish_test_item(self.test_id, self.now(), status)


    def close(self):
        self.rp_service.finish_launch(self.now())


    def now(self):
        time_now = str(int(time() * 1000))

        return time_now


    # Mapping should be used instead of this.
    def attribute_status(self, status):
        if status == "PASS":
            rp_status = "PASSED"
        else:
            rp_status = "FAILED"

        return rp_status


    def find_parent_suite_for_suite(self, suite):
        suite_count = len(self.scenario_info)
        for i in range(0, suite_count):
            if suite in self.scenario_info[i]['child_suites']:
                return self.scenario_info[i]['rp_id']
        # if suite is not a child, return None for parent suite id
        return None


    def find_parent_suite_for_test(self, test):
        suite_count = len(self.scenario_info)
        for i in range(0, suite_count):
            if test in self.scenario_info[i]['tests']:
                return self.scenario_info[i]['rp_id']
        # I don't think it should ever get this far. Test _should_ be part of a suite?
        return None


    def standardise_string(self, string):
        string = string.lower().replace(' ', '_')
        return string