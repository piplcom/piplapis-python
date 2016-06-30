from piplapis.data.utils import Serializable


class APIError(Exception, Serializable):
    
    """An exception raised when the response from the API contains an error."""
    
    def __init__(self, error, http_status_code, warnings=None):
        """Extend Exception.__init___ and set two extra attributes - 
        error (unicode) and http_status_code (int)."""
        Exception.__init__(self, error)
        self.error = error
        self.http_status_code = http_status_code
        self.warnings = warnings
        self.qps_allotted = None  # Your permitted queries per second
        self.qps_current = None  # The number of queries that you've run in the same second as this one.
        self.quota_allotted = None  # Your API quota
        self.quota_current = None  # The API quota used so far
        self.quota_reset = None  # The time when your quota resets
    
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

    def add_quota_and_throttle_data(self, quota_allotted, quota_current, qps_allotted, qps_current, quota_reset):
        # Get headers
        self.quota_allotted = quota_allotted
        self.quota_current = quota_current
        self.qps_allotted = qps_allotted
        self.qps_current = qps_current
        self.quota_reset = quota_reset
