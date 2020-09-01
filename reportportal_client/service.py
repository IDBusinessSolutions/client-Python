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

import json
import requests
import uuid
import pkg_resources
import platform
from time import time
from robot.api import logger

import six
from six.moves.collections_abc import Mapping
from requests.adapters import HTTPAdapter

from utilities import uri_join, _get_id, _get_msg, _dict_to_payload, _get_json, _get_data, _suite_path_to_list, standardise_suite_name
from client_base import ReportPortalServiceBase


POST_LOGBATCH_RETRY_COUNT = 10

#logger = logging.getLogger(__name__)
#logger.addHandler(logging.NullHandler())


class ReportPortalResultsReportingService(ReportPortalServiceBase):
    """Service class with report portal event callbacks."""

    # Status mapping to translate Robot Framework status to one recognised by Report Portal
    status_mapping = {
        "PASS": "PASSED",
        "FAIL": "FAILED",
        "SKIP": "SKIPPED"
    }

    def __init__(self,
                 endpoint,
                 project,
                 token,
                 log_batch_size=20,
                 is_skipped_an_issue=True,
                 verify_ssl=True,
                 retries=None):
        """Init the service class.

        Args:
            endpoint: endpoint of report portal service.
            project: project name to use for launch names.
            token: authorization token.
            log_batch_size: option to set the maximum number of logs
                            that can be processed in one batch
            is_skipped_an_issue: option to mark skipped tests as not
                'To Investigate' items on Server side.
            verify_ssl: option to not verify ssl certificates
        """
        self._batch_logs = []
        self.endpoint = endpoint
        self.log_batch_size = log_batch_size
        super(ReportPortalResultsReportingService, self).__init__(endpoint, token, verify_ssl=verify_ssl,
                                                                  retries=retries)
        self.project = project
        self.is_skipped_an_issue = is_skipped_an_issue
        self.base_url_v1 = uri_join(self.endpoint, "api/v1", self.project)
        self.base_url_v2 = uri_join(self.endpoint, "api/v2", self.project)
        self.base_project_url_v1 = self.base_url_v1
        self.base_project_url_v2 = self.base_url_v2
        self.max_pool_size = 50

        self.session = requests.Session()
        if retries:
            self.session.mount('https://', HTTPAdapter(
                max_retries=retries, pool_maxsize=self.max_pool_size))
            self.session.mount('http://', HTTPAdapter(
                max_retries=retries, pool_maxsize=self.max_pool_size))
        self.session.headers["Authorization"] = "bearer {0}".format(self.token)
        self.launch_id = None
        self.verify_ssl = verify_ssl

    def terminate(self, *args, **kwargs):
        """Call this to terminate the service."""
        pass
        self.base_project_url_v1 = uri_join(self.base_url_v1, self.project)
        self.base_project_url_v2 = uri_join(self.base_url_v2, self.project)
        self.launch_uuid = None

    def start_launch(self,
                     name,
                     start_time,
                     description=None,
                     attributes=None,
                     mode=None):
        """Start a new launch with the given parameters."""
        if attributes and isinstance(attributes, dict):
            attributes = _dict_to_payload(attributes)
        data = {
            "name": name,
            "description": description,
            "attributes": attributes,
            "startTime": start_time,
            "mode": mode
        }
        url = uri_join(self.base_project_url_v2, "launch")
        r = self.post_to_url(url, data)
        self.launch_uuid = _get_id(r)
        logger.debug("start_launch - ID: {}".format(self.launch_uuid))
        return self.launch_uuid

    def get_launch_internal_id(self):
        """Get the internal id for the currently active launch
        """
        url = uri_join(self.base_project_url_v1, "launch", "uuid", self.launch_uuid)
        r = self.get_from_url(url)
        launch_internal_id = _get_id(r)
        logger.debug("get_launch_internal_id - ID: %s", launch_internal_id)
        return launch_internal_id

    def get_root_suites(self):
        """Get the root level suites for the currently active launch
        """
        url = uri_join(self.base_project_url_v1, "item")

        logger.debug("Get Root suites URL: {}".format(url))
        parameters = {
            "filter.eq.launchId": self.get_launch_internal_id(),
            "filter.eq.type": "SUITE"
        }
        logger.debug(parameters)
        r = self.get_from_url(url, parameters=parameters)
        content = _get_json(r)['content']
        logger.debug("Root suites: ".format(content))

        return content

    def get_uu_id(self, id):
        """Get the UUID for a test item with known id
                """
        url = uri_join(self.base_project_url_v1, "item", id)

        r = self.get_from_url(url)
        uuid = _get_json(r)['uuid']
        logger.debug("Root suites: ".format(uuid))

        return uuid

    def get_child_suites(self, suite_id):
        """Get child test suites for a given suite
        """
        url = uri_join(self.base_project_url_v1, "item")
        parameters = {
            "filter.eq.launchId": self.get_launch_internal_id(),
            "filter.eq.parentId": suite_id,
            "filter.eq.type": "SUITE"
        }
        r = self.get_from_url(url, parameters=parameters)
        content = _get_json(r)['content']
        logger.debug("get_child_suites for suite_id {} from URL: {}".format(suite_id, url))
        logger.debug("get_child_suites: Child suites: {}".format(content))

        return content

    def get_parent_suite_uuid(self, test_path):
        """Get parent suite id for test
        """

        parent_suite_name = test_path[-2]
        url = uri_join(self.base_project_url_v1, "item")
        parameters = {
            "filter.eq.launchId": self.get_launch_internal_id(),
            "filter.eq.name": parent_suite_name,
            "filter.eq.type": "SUITE"
        }
        r = self.get_from_url(url, parameters=parameters)
        id = _get_json(r)['content'][0]['id']

        url = uri_join(self.base_project_url_v1, "item", id)

        r = self.get_from_url(url, parameters=parameters)
        uuid = _get_json(r)['uuid']

        return uuid


    def get_suite_id(self, suite_path):
        """Gets suite id for a given suite_path, and creates any suites that don't exist
        """

        # suite path is not itterable, so create list
        suite_path = _suite_path_to_list(suite_path)
        root_suite = standardise_suite_name(suite_path[0])

        # Look in root for highest level suite
        root_suites = self.get_root_suites()
        current_suite_id = None
        current_suite_uuid = None
        found = False
        logger.debug("get_suite_id: root suites: {}".format(root_suites))

        # Look for top level suite in RP launch root suites. (suite is a dict)
        for suite in root_suites:
            # remove .robot from suite name
            suite_name = standardise_suite_name(suite['name'])

            if suite_name == root_suite:
                current_suite_id = suite['id']
                current_suite_uuid = self.get_uu_id(current_suite_id)
                found = True
                logger.debug("get_suite_id: found high level suite at root launch level")
                break

        # If root suite doesn't already exist, create it and subsequent suites
        if not found:
            current_suite_uuid = self.start_test_item(root_suite, self.now(), "SUITE")
            logger.debug(current_suite_uuid)
            # By this point the root-level suite has just been created, so each remaining suite needs creating too
            if len(suite_path) > 1:
                for path_element in suite_path[1:]:
                    path_element = standardise_suite_name(path_element)
                    current_suite_uuid = self.start_test_item(path_element, self.now(), "SUITE", parent_item_id=current_suite_uuid)

        # By this point the root suit has either been created or already existed
        # If there are further suites, see if they exist, or create them
        # If the root suite already existed, we need to check to see if the remaning child suites exist.
        else:
            if len(suite_path) > 1:
                # Find or create child suites for remainder of the suite path
                for path_element in suite_path[1:]:
                    found = False
                    child_suites = self.get_child_suites(current_suite_id)
                    for suite in child_suites:
                        # suite is a dict
                        if suite['name'].lower() == path_element.lower():
                            current_suite_id = suite['id']
                            current_suite_uuid = self.get_uu_id(current_suite_id)
                            found = True
                            break
                    if not found:
                        # Create suite
                        current_suite_id = self.start_test_item(path_element, self.now(), "SUITE", parent_item_id=current_suite_uuid)

        return current_suite_uuid


    def now(self):
        time_now = str(int(time() * 1000))

        return time_now



    def connect_to_launch(self, launch_uuid):
        """Connects to a running launch using its UUID."""
        self.launch_uuid = launch_uuid
        logger.debug("connected_to_launch - ID: %s", self.launch_uuid)

    def finish_launch(self, end_time, status=None):
        """Finish a launch with the given parameters.

        Status can be one of the followings:
        (PASSED, FAILED, STOPPED, SKIPPED, RESETED, CANCELLED)
        """
        # process log batches firstly:
        if self._batch_logs:
            self.log_batch([], force=True)
        data = {
            "endTime": end_time,
            "status": status
        }
        url = uri_join(self.base_project_url_v1, "launch", self.launch_uuid, "finish")
        r = self.put_to_url(url, data)
        logger.debug("finish_launch - ID: {}".format(self.launch_uuid))
        return _get_msg(r)

    def start_test_item(self,
                        name,
                        start_time,
                        item_type,
                        description=None,
                        attributes=None,
                        parameters=None,
                        parent_item_id=None,
                        has_stats=True):
        """
        Item_type can be.

        (SUITE, STORY, TEST, SCENARIO, STEP, BEFORE_CLASS,
        BEFORE_GROUPS, BEFORE_METHOD, BEFORE_SUITE, BEFORE_TEST, AFTER_CLASS,
        AFTER_GROUPS, AFTER_METHOD, AFTER_SUITE, AFTER_TEST).

        attributes and parameters should be a dictionary
        with the following format:
            {
                "<key1>": "<value1>",
                "<key2>": "<value2>",
                ...
            }
        """
        if attributes and isinstance(attributes, dict):
            attributes = _dict_to_payload(attributes)
        if parameters:
            parameters = _dict_to_payload(parameters)

        data = {
            "name": name,
            "description": description,
            "attributes": attributes,
            "startTime": start_time,
            "launchUuid": self.launch_uuid,
            "type": item_type,
            "parameters": parameters,
            "hasStats": has_stats
        }
        if parent_item_id:
            url = uri_join(self.base_project_url_v2, "item", parent_item_id)
        else:
            url = uri_join(self.base_project_url_v2, "item")
        r = self.post_to_url(url, data)

        item_id = _get_id(r)
        logger.debug("start_test_item - ID: %s", item_id)
        return item_id

    def update_test_item(self, item_uuid, attributes=None, description=None):
        """Update existing test item at the Report Portal.

        :param str item_uuid:   Test item UUID returned on the item start
        :param str description: Test item description
        :param list attributes: Test item attributes
                                [{'key': 'k_name', 'value': 'k_value'}, ...]
        """
        data = {
            "description": description,
            "attributes": attributes,
        }
        item_id = self.get_item_id_by_uuid(item_uuid)
        url = uri_join(self.base_project_url_v1, "item", item_id, "update")
        r = self.put_to_url(url, data)
        logger.debug("update_test_item - Item: %s", item_id)
        return _get_msg(r)

    def finish_test_item(self,
                         item_id,
                         end_time,
                         status,
                         issue=None,
                         attributes=None):
        """Finish the test item and return HTTP response.

        :param item_id:    id of the test item
        :param end_time:   time in UTC format
        :param status:     status of the test
        :param issue:      description of an issue
        :param attributes: list of attributes
        :return:           json message

        """
        # check if skipped test should not be marked as "TO INVESTIGATE"
        if issue is None and status == "SKIPPED" \
                and not self.is_skipped_an_issue:
            issue = {"issue_type": "NOT_ISSUE"}

        if attributes and isinstance(attributes, dict):
            attributes = _dict_to_payload(attributes)

        data = {
            "endTime": end_time,
            "status": status,
            "issue": issue,
            "launchUuid": self.launch_uuid,
            "attributes": attributes
        }
        url = uri_join(self.base_project_url_v2, "item", item_id)
        r = self.put_to_url(url, data)
        logger.debug("finish_test_item - ID: %s", item_id)
        return _get_msg(r)

    def get_item_id_by_uuid(self, item_uuid):
        """Get test item ID by the given UUID.

        :param str item_uuid: UUID returned on the item start
        :return str:     Test item id
        """
        url = uri_join(self.base_project_url_v1, "item", "uuid", item_uuid)
        r = self.get_from_url(url)
        return _get_json(r)["id"]

    def get_project_settings(self):
        """
        Get settings from project.

        :return: json body
        """
        url = uri_join(self.base_project_url_v1, "settings")
        r = self.get_from_url(url)
        logger.debug("settings")
        return _get_json(r)

    def log(self, time, message, level=None, attachment=None, item_id=None):
        """
        Create log for test.

        :param time: time in UTC
        :param message: description
        :param level:
        :param attachment: files
        :param item_id:  id of item
        :return: id of item from response
        """
        data = {
            "launchUuid": self.launch_uuid,
            "time": time,
            "message": message,
            "level": level,
        }
        if item_id:
            data["itemUuid"] = item_id
        if attachment:
            data["attachment"] = attachment
            return self.log_batch([data], item_id=item_id)
        else:
            url = uri_join(self.base_project_url_v2, "log")
            r = self.post_to_url(url, data)
            logger.debug("log - ID: %s", item_id)
            return _get_id(r)

    def log_batch(self, log_data, item_id=None, force=False):
        """
        Log batch of messages with attachment.

        Args:
        log_data: list of log records.
            log record is a dict of;
                time, message, level, attachment
                attachment is a dict of:
                    name: name of attachment
                    data: fileobj or content
                    mime: content type for attachment
        item_id: UUID of the test item that owns log_data
        force:   Flag that forces client to process all the logs
                 stored in self._batch_logs immediately
        """
        self._batch_logs += log_data
        if len(self._batch_logs) < self.log_batch_size and not force:
            return
        url = uri_join(self.base_project_url_v2, "log")


        attachments = []
        for log_item in self._batch_logs:
            if item_id:
                log_item["itemUuid"] = item_id
            log_item["launchUuid"] = self.launch_uuid
            attachment = log_item.get("attachment", None)

            if "attachment" in log_item:
                del log_item["attachment"]

            if attachment:
                if not isinstance(attachment, Mapping):
                    attachment = {"data": attachment}

                name = attachment.get("name", str(uuid.uuid4()))
                log_item["file"] = {"name": name}
                attachments.append(("file", (
                    name,
                    attachment["data"],
                    attachment.get("mime", "application/octet-stream")
                )))

        files = [(
            "json_request_part", (
                None,
                json.dumps(self._batch_logs),
                "application/json"
            )
        )]
        files.extend(attachments)
        r = None
        for i in range(POST_LOGBATCH_RETRY_COUNT):
            try:
                r = self.session.post(
                    url=url,
                    files=files,
                    verify=self.verify_ssl
                )
                logger.debug("log_batch - ID: %s", item_id)
                #logger.debug("log_batch response: %s", r.text)
                self._batch_logs = []
                return _get_data(r)
            except KeyError:
                if i < POST_LOGBATCH_RETRY_COUNT - 1:
                    continue
                else:
                    raise

    @staticmethod
    def get_system_information(agent_name='agent_name'):
        """
        Get system information about agent, os, cpu, system, etc.

        :param agent_name: Name of the agent: pytest-reportportal,
                              roborframework-reportportal,
                              nosetest-reportportal,
                              behave-reportportal
        :return: dict {'agent': pytest-pytest 5.0.5,
                       'os': 'Windows',
                       'cpu': 'AMD',
                       'machine': "Windows10_pc"}
        """
        try:
            agent_version = pkg_resources.get_distribution(
                agent_name).version
            agent = '{0}-{1}'.format(agent_name, agent_version)
        except pkg_resources.DistributionNotFound:
            agent = 'not found'

        return {'agent': agent,
                'os': platform.system(),
                'cpu': platform.processor(),
                'machine': platform.machine()}
