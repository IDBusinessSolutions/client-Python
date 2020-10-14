
from .utilities import uri_join, _get_id, _get_msg, _dict_to_payload, _get_json, _get_data
from .client_base import ReportPortalServiceBase


class ReportPortalAdministrationService(ReportPortalServiceBase):
    """Service class with report portal event callbacks."""

    def __init__(self,
                 endpoint,
                 token,
                 verify_ssl=True,
                 retries=None):
        """Init the service class.

        Args:
            endpoint: endpoint of report portal service.
            project: project name to use for launch names.
            token: authorization token.
            is_skipped_an_issue: option to mark skipped tests as not
                'To Investigate' items on Server side.
            verify_ssl: option to not verify ssl certificates
        """
        super(ReportPortalAdministrationService, self).__init__(endpoint, token, verify_ssl=verify_ssl, retries=retries)

    def get_all_project_names(self):
        url = uri_join(self.base_url_v1, 'project', 'names')
        response = self.get_from_url(url)
        return _get_json(response)

    def create_project(self, project_name):
        url = uri_join(self.base_url_v1, "project")
        data = {
          "entryType": "INTERNAL",
          "projectName": "{}".format(project_name)
        }
        response = self.post_to_url(url, data)
        return response

    def delete_project(self, project_id):
        url = uri_join(self.base_url_v1, 'project', project_id)
        data = {
          "projectId": "{}".format(project_id)
        }
        response = self.delete_url(url, data)
        return response

    def update_project_settings(self, project_name, settings):
        url = uri_join(self.base_url_v1, 'project', project_name)
        data = settings
        response = self.put_to_url(url, data)

        return response
