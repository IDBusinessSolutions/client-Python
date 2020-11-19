import unittest
from uuid import UUID
from datetime import datetime

from reportportal_client import ReportPortalResultsReportingService, ReportPortalAdministrationService
from reportportal_client.utilities import _get_id, _get_json
from reportportal_client.client_base import ReportPortalError
from reportportal_client.helpers import gen_attributes
from config import *


class reporportal_clientStartLaunch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = ReportPortalResultsReportingService(endpoint, project, token)

    @classmethod
    def tearDownClass(cls):
        cls.service.finish_launch(datetime.now())
        cls.service.terminate()


    def test_start_launch(self):
        self.launch_id = self.service.start_launch(launch_name, datetime.utcnow())
        assert UUID(self.launch_id)


class reporportal_clientFinishLaunch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = ReportPortalResultsReportingService(endpoint, project, token)
        cls.launch_id = cls.service.start_launch(launch_name, datetime.utcnow())

    @classmethod
    def tearDownClass(cls):
        cls.service.terminate()


    def test_finish_launch(self):
        response = self.service.finish_launch(datetime.utcnow())
        assert response.get('id') == self.launch_id


class reportportal_clientMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = ReportPortalResultsReportingService(endpoint, project, token)
        cls.launch_id = cls.service.start_launch(launch_name, datetime.utcnow())

        # Create test items to allow getting test data and runing of child items
        cls.test_suite_1_name = 'test_suite_1'
        cls.test_suite_1_uuid = cls.service.start_test_item(cls.test_suite_1_name, datetime.utcnow(), 'SUITE')
        cls.test_suite_1_internal_id = cls.service.get_item_id_by_uuid(cls.test_suite_1_uuid)

        cls.test_suite_2_name = 'test_suite_2'
        cls.test_suite_2_uuid = cls.service.start_test_item(cls.test_suite_2_name, datetime.utcnow(), 'SUITE', parent_item_id=cls.test_suite_1_uuid)
        cls.test_suite_2_internal_id = cls.service.get_item_id_by_uuid(cls.test_suite_2_uuid)

        cls.test_test_name = 'test_test'
        cls.test_test_uuid = cls.service.start_test_item(cls.test_test_name, datetime.utcnow(), 'TEST', parent_item_id=cls.test_suite_2_uuid)

        # Create additional test item to allow testing of finish_test_item
        cls.existing_test_name = 'Existing test'
        cls.existing_test_id = cls.service.start_test_item(cls.existing_test_name, datetime.utcnow(), 'TEST')


    @classmethod
    def tearDownClass(cls):
        cls.service.finish_test_item(cls.test_test_uuid, datetime.utcnow(), 'SKIPPED')
        cls.service.finish_test_item(cls.test_suite_1_uuid, datetime.utcnow(), 'SKIPPED')
        cls.service.finish_test_item(cls.test_suite_2_uuid, datetime.utcnow(), 'SKIPPED')

        cls.service.finish_launch(datetime.utcnow())
        cls.service.terminate()

    def test_get_launch_internal_id(self):
        id = self.service.get_launch_internal_id()
        assert isinstance(id, int)

    def test_get_root_suites(self):
        root_suites = self.service.get_root_suites()
        assert root_suites[0]['name'] == self.test_suite_1_name

    def test_get_child_suites(self):
        child_suites = self.service.get_child_suites(self.test_suite_1_internal_id)
        assert child_suites[0]['name'] == self.test_suite_2_name

    def test_get_parent_suite_uuid(self):
        test_path = [self.test_suite_1_name, self.test_suite_2_name, self.test_test_name]
        parent_uuid = self.service.get_parent_suite_uuid(test_path)
        assert parent_uuid == self.test_suite_2_uuid

    def test_get_parent_suite_uuid_incorrect_path(self):
        with self.assertRaisesRegex(Exception, 'list index out of range'):
            test_path = ['foo', 'bar', 'test']
            self.service.get_parent_suite_uuid(test_path)

    def test_suite_in_list_existing(self):
        list = self.service.get_child_suites(self.test_suite_1_internal_id)
        suite_uuid = self.service.suite_in_list(list, self.test_suite_2_name, datetime.utcnow())
        assert suite_uuid == self.test_suite_2_uuid

    def test_suite_in_list_non_existing(self):
        list = self.service.get_child_suites(self.test_suite_1_internal_id)
        suite_uuid = self.service.suite_in_list(list, 'test_suite_3', datetime.utcnow())
        assert UUID(suite_uuid) and suite_uuid != self.test_suite_1_uuid != self.test_suite_2_uuid

    def test_get_suite_id_existing(self):
        list = [self.test_suite_1_name, self.test_suite_2_name]
        suite_uuid = self.service.get_suite_id(list, datetime.utcnow())
        assert suite_uuid == self.test_suite_2_uuid

    def test_get_suite_id_non_existing(self):
        list = [self.test_suite_1_name, self.test_suite_2_name, 'test_suite_4']
        suite_uuid = self.service.get_suite_id(list, datetime.utcnow())
        assert UUID(suite_uuid) and suite_uuid != self.test_suite_1_uuid != self.test_suite_2_uuid

    def test_start_test_item_suite(self):
        suite_id = self.service.start_test_item('Start Suite test', datetime.utcnow(), 'SUITE')
        assert UUID(suite_id)
        
    def test_start_test_item_test(self):
        test_id = self.service.start_test_item('Start Test test', datetime.utcnow(), 'TEST', parent_item_id=self.test_suite_1_uuid)
        assert UUID(test_id)

    def test_start_test_item_test_invalid_parent(self):
        with self.assertRaisesRegex(Exception, 'Did you use correct Test Item ID'):
            self.service.start_test_item('Start Test test', datetime.utcnow(), 'TEST',
                                                   parent_item_id='52a568ec-fd8c-11ea-adc1-0242ac120002')

    def test_start_test_item_keyword(self):
        keyword_id = self.service.start_test_item('Start Test keyword', datetime.utcnow(), 'STEP', parent_item_id=self.test_test_uuid)
        assert UUID(keyword_id)
    
    def test_finish_test_item_test(self):
        response = self.service.finish_test_item(self.existing_test_id, datetime.utcnow(), 'SKIPPED')
        assert 'successfully finished' in response.get('message')

    def test_get_item_id_by_uuid(self):
        id = self.service.get_item_id_by_uuid(self.test_suite_1_uuid)
        assert isinstance(id, int)

    def test_log(self):
        log_id = self.service.log(datetime.utcnow(), 'This is a log message', level='INFO',
                                  item_id=self.test_suite_1_uuid)
        assert UUID(log_id)


class reportportal_clientAdminMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        now = datetime.utcnow().strftime('%d%m%y_%H%M%S')
        cls.admin_service = ReportPortalAdministrationService(endpoint, token)
        cls.project_name_1 = "python_client_1{}".format(now)
        cls.project_name_2 = "python_client_2{}".format(now)
        cls.project_name_3 = "python_client_3{}".format(now)
        cls.project_name_4 = "python.client.4{}".format(now)

        # create 2 projects for use in tests
        cls.project_1_id = _get_id(cls.admin_service.create_project(cls.project_name_1))
        cls.project_2_id = _get_id(cls.admin_service.create_project(cls.project_name_2))


    @classmethod
    def tearDownClass(cls):
        cls.admin_service.delete_project(cls.project_1_id)
        cls.admin_service.delete_project(cls.project_2_id)

    def test_get_all_project_names(self):
        projects = self.admin_service.get_all_project_names()
        self.assertIsInstance(projects, list)

    def test_create_project(self):
        response = self.admin_service.create_project(self.project_name_3)
        self.project_3_id = _get_id(response)
        self.assertIsInstance(self.project_3_id, int)

    def test_create_project_invalid_name(self):
        with self.assertRaises(ReportPortalError):
            self.admin_service.create_project(self.project_name_2)

    def test_update_project_settings(self):
        settings = {
                      "configuration": {
                        "attributes": {
                          "job.keepLaunches": "Forever"
                        }
                      }
                    }
        response = self.admin_service.update_project_settings(self.project_name_1, settings)
        message = _get_json(response)['message']
        self.assertEqual(message, "Project with name = '{}' is successfully updated.".format(self.project_name_1))

    def test_delete_project(self):
        response = self.admin_service.delete_project(self.project_2_id)
        message = _get_json(response)['message']
        self.assertEqual(message, "Project with id = '{}' has been successfully deleted.".format(self.project_2_id))

class reportportal_clientHelperMethods(unittest.TestCase):

    def test_tag_attritubes(self):
        tags = ['foo', 'BAR', 'Spam', 'eggs']
        # Report Portal expects tag list to be in a particular format
        if tags:
            tags[0] = 'tag_list:{}'.format(tags[0])
        tags_rp = gen_attributes(tags)
        assert tags_rp == [{'key': 'tag_list', 'value': 'foo'}, {'value': 'BAR'}, {'value': 'Spam'}, {'value': 'eggs'}]

if __name__ == '__main__':
    unittest.main()
