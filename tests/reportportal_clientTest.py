import unittest
from uuid import UUID
from datetime import datetime

from reportportal_client import ReportPortalResultsReportingService
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
        try:
            test_path = ['foo', 'bar', 'test']
            self.service.get_parent_suite_uuid(test_path)
            error_message = None
        except Exception as e:
            error_message = e.message
        assert 'list index out of range' in error_message

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
        try:
            self.service.start_test_item('Start Test test', datetime.utcnow(), 'TEST',
                                                   parent_item_id='52a568ec-fd8c-11ea-adc1-0242ac120002')
            error_message = None
        except Exception as e:
            error_message = e.message

        assert 'Did you use correct Test Item ID' in error_message

    def test_start_test_item_keyword(self):
        keyword_id = self.service.start_test_item('Start Test keyword', datetime.utcnow(), 'STEP', parent_item_id=self.test_test_uuid)
        assert UUID(keyword_id)
    
    def test_finish_test_item_test(self):
        response = self.service.finish_test_item(self.existing_test_id, datetime.utcnow(), 'SKIPPED')
        print(response)
        assert 'successfully finished' in response.get('message')

    def test_get_item_id_by_uuid(self):
        id = self.service.get_item_id_by_uuid(self.test_suite_1_uuid)
        assert isinstance(id, int)

    def test_log(self):
        log_id = self.service.log(datetime.utcnow(), 'This is a log message', level='INFO',
                                  item_id=self.test_suite_1_uuid)
        assert UUID(log_id)

if __name__ == '__main__':
    unittest.main()