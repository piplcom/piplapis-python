import logging

from piplapis.data.utils import Serializable


logger = logging.getLogger(__name__)


class APIError(Exception, Serializable):
    
    """An exception raised when the response from the API contains an error."""
    
    def __init__(self, error, http_status_code, warnings=None):
        """Extend Exception.__init___ and set two extra attributes - 
        error (unicode) and http_status_code (int)."""
        Exception.__init__(self, error)
        self.error = error
        self.http_status_code = http_status_code
        self.warnings = warnings

        # HTTP headers
        self.qps_allotted = None  # Your permitted queries per second
        self.qps_current = None  # The number of queries that you've run in the same second as this one.
        self.qps_live_allotted = None  # Your permitted queries per second
        self.qps_live_current = None  # The number of queries that you've run in the same second as this one.
        self.qps_demo_allotted = None  # Your permitted queries per second
        self.qps_demo_current = None  # The number of queries that you've run in the same second as this one.
        self.quota_allotted = None  # Your API quota
        self.quota_current = None  # The API quota used so far
        self.quota_reset = None  # The time when your quota resets
        self.demo_usage_allotted = None  # Your permitted demo queries
        self.demo_usage_current = None  # The number of demo queries that you've already run
        self.demo_usage_expiry = None  # The expiry time of your demo usage
    
    @property
    def is_user_error(self):
        """A bool that indicates whether the error is on the user's side."""
        return 400 <= self.http_status_code < 500
    
    @property
    def is_pipl_error(self):
        """A bool that indicates whether the error is on Pipl's side."""
        return not self.is_user_error
    
    @classmethod
    def from_dict(cls, d):
        """Transform the dict to a error object and return the error."""
        return cls(d.get('error'), d.get('@http_status_code'), d.get('warnings'))
    
    def to_dict(self):
        """Return a dict representation of the error."""
        return {'error': self.error,
                '@http_status_code': self.http_status_code,
                'warnings': self.warnings}

    def add_quota_throttle_data(self, *args, **kwargs):
        logger.warn("APIError.add_quota_throttle_data is deprecated")
        return self._add_rate_limiting_headers(*args, **kwargs)

    def _add_rate_limiting_headers(self, quota_allotted=None, quota_current=None, quota_reset=None, qps_allotted=None,
                                   qps_current=None, qps_live_allotted=None, qps_live_current=None,
                                   qps_demo_allotted=None,
                                   qps_demo_current=None, demo_usage_allotted=None, demo_usage_current=None,
                                   demo_usage_expiry=None):
        self.qps_allotted = qps_allotted
        self.qps_current = qps_current
        self.qps_live_allotted = qps_live_allotted
        self.qps_live_current = qps_live_current
        self.qps_demo_allotted = qps_demo_allotted
        self.qps_demo_current = qps_demo_current
        self.quota_allotted = quota_allotted
        self.quota_current = quota_current
        self.quota_reset = quota_reset
        self.demo_usage_allotted = demo_usage_allotted
        self.demo_usage_current = demo_usage_current
        self.demo_usage_expiry = demo_usage_expiry
