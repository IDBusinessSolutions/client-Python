import os
import traceback
from mimetypes import guess_type
from time import time, sleep
from reportportal_client import ReportPortalResultsReportingService


def timestamp():
    return str(int(time() * 1000))


endpoint = "http://report-portal.idbs-dev.com"
project = "tara_integration"
# You can get UUID from user profile page in the Report Portal.
token = "42c4195e-ecea-44f7-af51-09e861516863"
launch_name = "Test launch"
launch_doc = "Testing logging with attachment."


def my_error_handler(exc_info):
    """
    This callback function will be called by async service client when error occurs.
    Return True if error is not critical and you want to continue work.
    :param exc_info: result of sys.exc_info() -> (type, value, traceback)
    :return:
    """
    print("Error occurred: {}".format(exc_info[1]))
    traceback.print_exception(*exc_info)


# Report Portal versions >= 5.0.0:
service = ReportPortalResultsReportingService(endpoint=endpoint, project=project,
                                   token=token)

# Start launch.
launch = service.start_launch(name=launch_name,
                              start_time=timestamp(),
                              description=launch_doc)

print('Launch UUID: {0}'.format(launch))
print('Launch internal ID: {0}'.format(service.get_launch_internal_id()))

master_suite_id = service.start_test_item(name="Top level suite",
                                  description="Top level suite",
                                  start_time=timestamp(),
                                  item_type="SUITE",
                                  parameters={"key1": "val1",
                                              "key2": "val2"})

sub_suite_id = service.start_test_item(name="Second level suite",
                                       start_time=timestamp(),
                                       item_type="SUITE",
                                       parent_item_id=master_suite_id,
                                  parameters={"key1": "val1",
                                              "key2": "val2"})

test_id = service.start_test_item(name="Test 1",
                                  start_time=timestamp(),
                                  parent_item_id=sub_suite_id,
                                  item_type="TEST",
                                  parameters={"key1": "val1",
                                              "key2": "val2"})



item_id = service.start_test_item(name="Test Step",
                                  description="First Test Case",
                                  start_time=timestamp(),
                                  item_type="STEP",
                                  parent_item_id=test_id,
                                  parameters={"key1": "val1",
                                              "key2": "val2"})

child_step_item_id = service.start_test_item(name="Child Test Step",
                                  description="First Test Case",
                                  start_time=timestamp(),
                                  item_type="STEP",
                                  parent_item_id=item_id,
                                  parameters={"key1": "val1",
                                              "key2": "val2"})


# Create text log message with INFO level.
service.log(time=timestamp(),
            message="Hello World!",
            item_id=item_id,
            level="INFO")

# Create log message with attached text output and WARN level.
service.log(time=timestamp(),
            message="Too high memory usage!",
            level="WARN",
            item_id=item_id,
            attachment={
                "name": "free_memory.txt",
                "data": "This is a dummy text file.",
                "mime": "text/plain"
            })

# Create log message with binary file, INFO level and custom mimetype.
image = "image.png"
with open(image, "rb") as fh:
    attachment = {
        "name": os.path.basename(image),
        "data": fh.read(),
        "mime": guess_type(image)[0] or "application/octet-stream"
    }
    service.log(timestamp(), "Screen shot of issue.", "INFO", attachment, item_id=item_id,)

# Create log message supplying only contents
service.log(
    timestamp(),
    "running processes",
    "INFO",
    item_id=item_id,
    attachment="Running processes")

# Finish test item Report Portal versions >= 5.0.0.
service.finish_test_item(item_id=child_step_item_id, end_time=timestamp(), status="PASSED")

sleep(1)

#service.finish_test_item(item_id=item_id, end_time=timestamp(), status="PASSED")

sleep(1)

#service.finish_test_item(item_id=test_id, end_time=timestamp(), status="PASSED")

sleep(1)

#service.finish_test_item(item_id=sub_suite_id, end_time=timestamp(), status="PASSED")

sleep(1)

#service.finish_test_item(item_id=master_suite_id, end_time=timestamp(), status="PASSED")

sub_suite_id = service.start_test_item(name="Second level suite 2",
                                       start_time=timestamp(),
                                       item_type="SUITE",
                                       parent_item_id=master_suite_id,
                                  parameters={"key1": "val1",
                                              "key2": "val2"})

test_id = service.start_test_item(name="Test 2-1",
                                  start_time=timestamp(),
                                  parent_item_id=sub_suite_id,
                                  item_type="TEST",
                                  parameters={"key1": "val1",
                                              "key2": "val2"})
sleep(1)

#service.finish_test_item(item_id=test_id, end_time=timestamp(), status="PASSED")

sleep(1)

#service.finish_test_item(item_id=sub_suite_id, end_time=timestamp(), status="PASSED")

#service.finish_test_item(item_id=master_suite_id, end_time=timestamp(), status="PASSED")

# Finish launch.
service.finish_launch(end_time=timestamp())

print(service.get_root_suites())

for suite in service.get_root_suites():
    print("** {0} **".format(suite['name']))
    print(service.get_child_suites(suite['id']))

print(service.get_suite_id(['Top level suite', 'Second level suite']))

# Due to async nature of the service we need to call terminate() method which
# ensures all pending requests to server are processed.
# Failure to call terminate() may result in lost data.
service.terminate()