
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
