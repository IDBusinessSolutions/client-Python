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

from service import ReportPortalResultsReportingService
from administration import ReportPortalAdministrationService
import config
from time import time
from robot.api import logger

__all__ = ('ReportPortalResultsReportingService', 'ReportPortalAdministrationService', 'POST_LOGBATCH_RETRY_COUNT')

POST_LOGBATCH_RETRY_COUNT = 10

endpoint = config.endpoint
project = "tara_integration"
# You can get UUID from user profile page in the Report Portal.
token = config.token
launch_name = "RF Test launch"
launch_doc = "Testing RF tests."
launch_time = str(int(time() * 1000))


class reportportal_client:

    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, launch_id=None):

        if launch_id is None:
            self.rp_service = ReportPortalResultsReportingService(endpoint, project, token)
            self.launch_id = self.rp_service.start_launch(launch_name, launch_time, launch_doc)

            # Not sure what this is for
            self.current_test_id = None
            self.current_suites = {}

            # List for scenario info
            self.scenario_info = []
        else:
            self.launch_id = launch_id


    def start_suite(self, name, attributes):

        # If the suite is named "test_suites", we don't want a suite started in report portal
        if self.standardise_string(name) != "test_suites":
            # Gets suite ID if it exists, else starts the suite
            suite_id = self.rp_service.get_suite_id(attributes['source'])

            # Add RP suite id to list of currently running suites. This is to allow stop_suite to stop RP suite.
            self.current_suites[attributes['id']] = suite_id


    def end_suite(self, name, attributes):

        # Get RP test status from test status mapping
        status = self.attribute_status(attributes["status"])

        # Get RP suite id from dictionary of currently running suites
        suite_id = self.current_suites.get(attributes['id'])

        # Stop RP suite
        self.rp_service.finish_test_item(suite_id, self.now(), status)


    def start_test(self, name, attributes):

        # standardise test name
        name = self.standardise_string(name)

        # Check for Parent item ID
        parent_id = self.find_parent_suite_for_test(attributes['longname'])

        # Add tags to RP attributes (RP only accepts dictionary of attributes)
        tags_dict = {'tags': attributes['tags']}

        # Start test item
        self.current_test_id = self.rp_service.start_test_item(name, self.now(), "TEST", description=attributes['doc'], attributes=tags_dict, parent_item_id=parent_id)


    def end_test(self, name, attributes):
        status = self.attribute_status(attributes["status"])
        self.rp_service.finish_test_item(self.current_test_id, self.now(), status)


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


    def find_parent_suite_for_test(self, test_suite_path):
        """

        :param test_suite_path:
        :return:
        """
        test_suite_path = self.standardise_string(test_suite_path)
        # Mak list of parent suites from path
        suite_list = test_suite_path.split(".")
        # Find the RP ID of the last suite
        parent_suite_id = self.rp_service.get_parent_suite_id(suite_list)

        return parent_suite_id


    def standardise_string(self, string):
        string = string.lower().replace(' ', '_')
        return string

