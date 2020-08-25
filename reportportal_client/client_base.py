import requests
from requests.adapters import HTTPAdapter

from utilities import uri_join


class ReportPortalServiceBase(object):
    """Base Service class for interfacing with report portal."""

    def __init__(self,
                 endpoint,
                 token,
                 is_skipped_an_issue=True,
                 verify_ssl=True,
                 retries=None):
        """Init the service class.

        Args:
            endpoint: endpoint of report portal service.
            token: authorization token.
            is_skipped_an_issue: option to mark skipped tests as not
                'To Investigate' items on Server side.
            verify_ssl: option to not verify ssl certificates
        """
        super(ReportPortalServiceBase, self).__init__()
        self.endpoint = endpoint
        self.token = token
        self.is_skipped_an_issue = is_skipped_an_issue
        self.base_url_v1 = uri_join(self.endpoint, "api/v1")
        self.base_url_v2 = uri_join(self.endpoint, "api/v2")

        self.session = requests.Session()
        if retries:
            self.session.mount('https://', HTTPAdapter(max_retries=retries))
            self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.headers["Authorization"] = "bearer {0}".format(self.token)
        self.launch_uuid = None
        self.verify_ssl = verify_ssl

    def terminate(self, *args, **kwargs):
        """Call this to terminate the service."""
        pass

    def get_from_url(self, url, json_data=None, parameters=None):
        if json_data is None:
            json_data = {}
        if parameters is None:
            parameters = {}
        reply = self.session.get(url=url, json=json_data, params=parameters, verify=self.verify_ssl)
        return reply

    def put_to_url(self, url, json_data=None):
        if json_data is None:
            json_data = {}
        reply = self.session.put(url=url, json=json_data, verify=self.verify_ssl)
        return reply

    def post_to_url(self, url, json_data=None):
        if json_data is None:
            json_data = {}
        reply = self.session.post(url=url, json=json_data, verify=self.verify_ssl)
        return reply

    def delete_url(self, url, json_data=None):
        if json_data is None:
            json_data = {}
        reply = self.session.delete(url=url, json=json_data, verify=self.verify_ssl)
        return reply
