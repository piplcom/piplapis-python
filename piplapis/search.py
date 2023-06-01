"""Python wrapper for easily making calls to Pipl's Search API.

Pipl's Search API allows you to query with the information you have about
a person (his name, address, email, phone, username and more) and in response 
get all the data available on him on the web.

The classes contained in this module are:
- SearchAPIRequest -- Build your request and send it.
- SearchAPIResponse -- Holds the response from the API in case it contains data.
- SearchAPIError -- An exception raised when the API response is an error.

The classes are based on the person data-model that's implemented here in the
sub-package piplapis.data.

"""
import json

import datetime
import logging

import pytz as pytz

from six import string_types

try:
    import urllib.request as urllib2
    from urllib.parse import urlencode
except ImportError:
    import urllib2
    from urllib import urlencode

import urllib
import itertools
import threading

import piplapis
from piplapis.data.available_data import AvailableData
from piplapis.error import APIError
from piplapis.data import *
from piplapis.data.utils import Serializable

logger = logging.getLogger(__name__)


class SearchAPIRequest(object):
    """A request to Pipl's Search API.
    
    Building the request from the query parameters can be done in two ways:
    
    Option 1 - directly and quickly (for simple requests with only few 
               parameters):
            
    >>> from piplapis.search import SearchAPIRequest
    >>> request = SearchAPIRequest(api_key='YOURKEY', email='clark.kent@example.com')
    >>> response = request.send()
    
    Option 2 - using the data-model (useful for more complex queries; for 
               example, when there are multiple parameters of the same type 
               such as few phones or a few addresses or when you'd like to use 
               information beyond the usual identifiers such as name or email, 
               information like education, job, relationships etc):
            
    >>> from piplapis.search import SearchAPIRequest
    >>> from piplapis.data import Person, Name, Address, Job
    >>> fields = [Name(first='Clark', last='Kent'),
    >>>           Address(country='US', state='KS', city='Smallville'),
    >>>           Address(country='US', state='KS', city='Metropolis'),
    >>>           Job(title='Field Reporter')]
    >>> request = SearchAPIRequest(api_key='YOURKEY',
    >>>                            person=Person(fields=fields))
    >>> response = request.send()

    Sending the request and getting the response is very simple and can be done
    by either making a blocking call to request.send() or by making 
    a non-blocking call to request.send_async(callback) which sends the request 
    asynchronously.
    
    You can also set various request flags:
    minimum_probability - a float between 0 and 1, to define what statistical confidence you need for inferred data.
    show_sources - string, either "all", "matching" or True. If not set, no sources will be shown.
        "all" - all sources will be shown.
        "matching" - only sources belonging to a matching person will be shown.
        Boolean True will behave like "matching".
    hide_sponsored - boolean (default False), whether to hide sponsored results.
    infer_persons - boolean (default False),  whether the API should return person responses made up solely from data inferred by statistical analysis.
    minimum_match - a float between 0 and 1, to define the minimum match under which possible persons will not be returned.
    that may be the person you're looking for)
    live_feeds - boolean (default True), whether to use live data feeds. Can be turned off 
    for performance.
    """

    HEADERS = {'User-Agent': 'piplapis/python/%s' % piplapis.__version__}
    BASE_URL = '{}://api.pipl.com/search/?'

    # The following are default settings for all request objects
    # You can set them once instead of passing them to the constructor every time
    default_api_key = None
    default_use_https = False
    default_minimum_probability = None
    default_show_sources = None
    default_minimum_match = None
    default_top_match = None
    default_hide_sponsored = None
    default_live_feeds = None
    default_infer_persons = None
    default_match_requirements = None
    default_source_category_requirements = None
    default_response_class = None

    @classmethod
    def set_default_settings(cls, api_key=None, minimum_probability=None, show_sources=None,
                             minimum_match=None, hide_sponsored=None, live_feeds=None, use_https=False,
                             match_requirements=None, source_category_requirements=None, infer_persons=None,
                             top_match=None, response_class=None):
        cls.default_api_key = api_key
        cls.default_minimum_probability = minimum_probability
        cls.default_show_sources = show_sources
        cls.default_minimum_match = minimum_match
        cls.default_top_match = top_match
        cls.default_hide_sponsored = hide_sponsored
        cls.default_live_feeds = live_feeds
        cls.default_use_https = use_https
        cls.default_match_requirements = match_requirements
        cls.default_source_category_requirements = source_category_requirements
        cls.default_infer_persons = infer_persons
        cls.default_response_class = response_class

    def __init__(self, api_key=None, first_name=None, middle_name=None,
                 last_name=None, raw_name=None, email=None, phone=None, country_code=None,
                 raw_phone=None, username=None, user_id=None, country=None, state=None, city=None, house=None,
                 street=None, zip_code=None, raw_address=None, from_age=None, to_age=None, person=None, url=None,
                 search_pointer=None, minimum_probability=None, show_sources=None,
                 minimum_match=None, hide_sponsored=None, live_feeds=None, use_https=None,
                 match_requirements=None, source_category_requirements=None, infer_persons=None, top_match=None, response_class=None):
        """Initiate a new request object with given query params.
        
        Each request must have at least one searchable parameter, meaning 
        a name (at least first and last name), email, phone or username. 
        Multiple query params are possible (for example querying by both email 
        and phone of the person).
        
        Args:
        
        :param api_key: str, a valid API key.
                   Note that you can set a default API key 
                   (piplapis.search.default_api_key = '<your_key>') instead of 
                   passing it to each request object. 
        :param first_name: unicode, minimum 2 chars.
        :param middle_name: unicode. 
        :param last_name: unicode, minimum 2 chars.
        :param raw_name: unicode, an unparsed name containing at least a first name 
                    and a last name.
        :param email: unicode.
        :param phone: int/long. A national phone with no formatting.
        :param country_code: int. The phone country code
        :param raw_phone: string. A phone to be sent as-is, will be parsed by Pipl.
        :param username: unicode, minimum 3 chars.
        :param url: unicode, minimum 3 chars.
        :param user_id: unicode.
        :param country: unicode, a 2 letter country code from:
                   http://en.wikipedia.org/wiki/ISO_3166-2
        :param state: unicode, a state code from:
                 http://en.wikipedia.org/wiki/ISO_3166-2%3AUS
                 http://en.wikipedia.org/wiki/ISO_3166-2%3ACA
        :param city: unicode.
        :param street: unicode, minimum 2 chars.
        :param house: unicode.
        :param zip_code: int. Address zip code.
        :param raw_address: unicode, an unparsed address.
        :param from_age: int.
        :param to_age: int.
        :param person: A Person object (available at piplapis.data.Person).
                  The person can contain every field allowed by the data-model
                  (see piplapis.data.fields) and can hold multiple fields of
                  the same type (for example: two emails, three addresses etc.)
        :param search_pointer: str, sending a search pointer of a possible person will retrieve 
                          more data related to this person.
        :param minimum_probability: float (0-1). The minimum required confidence for inferred data.
        :param show_sources: str or bool, one of "matching"/"all". "all" will show all sources, "matching"
                        only those of the matching person. Boolean True will behave like "matching".
        :param minimum_match: float (0-1). The minimum required match under which possible persons will not be returned.
        :param live_feeds: bool, default True. Whether to use live feeds. Only relevant in plans that include
                      live feeds. Can be set to False for performance.
        :param hide_sponsored: bool, default False. Whether to hide sponsored results.
        :param infer_persons: bool, default False. Whether the API should return person responses made up solely from data inferred by statistical analysis.
        :param use_https: bool, default False. Whether to use an encrypted connection.
        :param match_requirements: str/unicode, a match requirements criteria. This criteria defines what fields
                                   must be present in an API response in order for it to be returned as a match.
                                   For example: "email" or "email or phone", or "email or (phone and name)"
        :param source_category_requirements: str/unicode, a source category requirements criteria. This criteria defines
                                   what source categories must be present in an API response in order for it to be
                                   returned as a match. For example: "personal_profiles" or "personal_profiles or professional_and_business"
        :param response_class: object, an object inheriting SearchAPIResponse and adding functionality beyond the basic
                            response scope. This provides the option to override methods or just add them.

        Each of the arguments that should have a unicode value accepts both
        unicode objects and utf8 encoded str (will be decoded automatically).
        """
        if person is None:
            person = Person()
        if first_name or middle_name or last_name:
            name = Name(first=first_name, middle=middle_name, last=last_name)
            person.add_fields([name])
        if raw_name:
            person.add_fields([Name(raw=raw_name)])
        if email:
            person.add_fields([Email(address=email)])
        if phone or raw_phone:
            person.add_fields([Phone(country_code=country_code, number=phone, raw=raw_phone)])
        if username:
            person.add_fields([Username(content=username)])
        if url:
            person.add_fields([URL(url=url)])
        if user_id:
            person.add_fields([UserID(content=user_id)])
        if country or state or city or house or street or zip_code:
            address = Address(country=country, state=state, city=city, house=house, street=street, zip_code=zip_code)
            person.add_fields([address])
        if raw_address:
            person.add_fields([Address(raw=raw_address)])
        if from_age is not None or to_age is not None:
            dob = DOB.from_age_range(from_age or 0, to_age or 1000)
            person.add_fields([dob])

        person.search_pointer = search_pointer
        self.person = person

        self.api_key = api_key or self.default_api_key
        self.show_sources = show_sources if show_sources is not None else self.default_show_sources
        self.live_feeds = live_feeds if live_feeds is not None else self.default_live_feeds
        self.minimum_match = minimum_match or self.default_minimum_match
        self.top_match = top_match or self.default_top_match
        self.minimum_probability = minimum_probability or self.default_minimum_probability
        self.hide_sponsored = hide_sponsored if hide_sponsored is not None else self.default_hide_sponsored
        self.match_requirements = match_requirements or self.default_match_requirements
        self.source_category_requirements = source_category_requirements or self.default_source_category_requirements
        self.use_https = use_https if use_https is not None else self.default_use_https
        self.infer_persons = infer_persons if infer_persons is not None else self.default_infer_persons

        response_class = response_class or self.default_response_class
        self.response_class = response_class if response_class and issubclass(response_class, SearchAPIResponse) \
            else SearchAPIResponse

    def validate_query_params(self, strict=True):
        """Check if the request is valid and can be sent, raise ValueError if 
        not.
        
        :param strict, boolean. If True, an exception is raised on every
        invalid query parameter, if False an exception is raised only when the search
        request cannot be performed because required query params are missing.
        
        """
        if not self.api_key:
            raise ValueError('API key is missing')
        if strict:
            if self.top_match and type(self.top_match) is not bool:
                raise ValueError('top_match should be a boolean')
            if self.minimum_match and (type(self.minimum_match) is not float or
                                       self.minimum_match > 1 or self.minimum_match < 0):
                raise ValueError('minimum_match should be a float between 0 and 1')
            if self.hide_sponsored is not None and type(self.hide_sponsored) is not bool:
                raise ValueError('hide_sponsored should be a boolean')
            if self.infer_persons is not None and type(self.infer_persons) is not bool:
                raise ValueError('infer_persons should be a boolean')
            if self.live_feeds is not None and type(self.live_feeds) is not bool:
                raise ValueError('live_feeds should be a boolean')
            if self.match_requirements is not None and not isinstance(self.match_requirements, string_types):
                raise ValueError('match_requirements should be an str or unicode object')
            if self.source_category_requirements is not None and not isinstance(self.source_category_requirements,
                                                                                string_types):
                raise ValueError('source_category_requirements should be an str or unicode object')
            if self.show_sources not in ("all", "matching", "false", "true", True, False, None):
                raise ValueError('show_sources has a wrong value. Should be "matching", "all", True, False or None')
            if self.minimum_probability and (type(self.minimum_probability) is not float or
                                             self.minimum_probability > 1 or self.minimum_probability < 0):
                raise ValueError('minimum_probability should be a float between 0 and 1')
            if self.person.unsearchable_fields and not self.person.is_searchable:
                raise ValueError('Some fields are unsearchable: %s' % self.person.unsearchable_fields)
        if not self.person.is_searchable:
            raise ValueError('No valid name/username/user_id/phone/email/address or search pointer in request')

    @property
    def url(self):
        """The URL of the request (str)."""
        query = self.get_search_query()
        return self.get_base_url() + urlencode(query, doseq=True)

    def get_search_query(self):
        query = {"key": self.api_key}
        if self.person and self.person.search_pointer:
            query['search_pointer'] = self.person.search_pointer
        elif self.person:
            query['person'] = self.person.to_json()
        if self.minimum_probability is not None:
            query['minimum_probability'] = self.minimum_probability
        if self.minimum_match is not None:
            query['minimum_match'] = self.minimum_match
        if self.top_match is not None:
            query['top_match'] = self.top_match
        if self.hide_sponsored is not None:
            query['hide_sponsored'] = self.hide_sponsored
        if self.infer_persons is not None:
            query['infer_persons'] = self.infer_persons
        if self.match_requirements is not None:
            query['match_requirements'] = self.match_requirements
        if self.source_category_requirements is not None:
            query['source_category_requirements'] = self.source_category_requirements
        if self.live_feeds is not None:
            query['live_feeds'] = self.live_feeds
        if self.show_sources is not None:
            query['show_sources'] = self.show_sources
        return query

    def send(self, strict_validation=True):
        """Send the request and return the response or raise SearchAPIError.
        
        calling this method blocks the program until the response is returned,
        if you want the request to be sent asynchronously please refer to the 
        send_async method. 
        
        the response is returned as a SearchAPIResponse object.
        
        :param strict_validation:  bool. Used by self.validate_query_params.
        
        :raises ValueError (raised from validate_query_params),
        httpError/URLError and SearchAPIError (when the response is returned 
        but contains an error).
        
        example:
        >>> from piplapis.search import SearchAPIRequest, SearchAPIError
        >>> request = SearchAPIRequest('YOURKEY', email='clark.kent@example.com')
        >>> try:
        ...     response = request.send()
        ... except SearchAPIError as e:
        ...     print e.http_status_code, e

        :return: A Response from the API
        :rtype: SearchAPIResponse
        """
        self.validate_query_params(strict=strict_validation)

        query = self.get_search_query()
        request = urllib2.Request(url=self.get_base_url(), data=urlencode(query, True).encode(),
                                  headers=SearchAPIRequest.HEADERS)
        try:
            response = urllib2.urlopen(request)
            json_response = response.read().decode()
            search_response = self.response_class.from_json(json_response)
            search_response._add_rate_limiting_headers(*self._get_quota_and_throttle_data(response.headers))
            return search_response
        except urllib2.HTTPError as e:
            json_error = e.read()
            if not json_error:
                raise e
            try:
                exception = SearchAPIError.from_json(json_error.decode())
                exception._add_rate_limiting_headers(*self._get_quota_and_throttle_data(e.headers))
                raise exception
            except ValueError:
                raise e

    @staticmethod
    def _get_quota_and_throttle_data(headers):

        # Set default values
        (quota_allotted, quota_current, quota_reset, qps_allotted, qps_current, qps_live_allotted, qps_live_current,
         qps_demo_allotted, qps_demo_current, demo_usage_allotted, demo_usage_current, demo_usage_expiry, package_allotted, package_current, package_expiry) = (None,) * 15

        time_format = "%A, %B %d, %Y %I:%M:%S %p %Z"

        # Handle quota headers
        if 'X-APIKey-Quota-Allotted' in headers:
            quota_allotted = int(headers.get('X-APIKey-Quota-Allotted'))
        if 'X-APIKey-Quota-Current' in headers:
            quota_current = int(headers.get('X-APIKey-Quota-Current'))
        if 'X-Quota-Reset' in headers:
            datetime_str = headers.get('X-Quota-Reset')
            quota_reset = datetime.datetime.strptime(datetime_str, time_format).replace(tzinfo=pytz.utc)

        # Handle throttling
        if 'X-QPS-Allotted' in headers:
            qps_allotted = int(headers.get('X-QPS-Allotted'))
        if 'X-QPS-Current' in headers:
            qps_current = int(headers.get('X-QPS-Current'))
        if 'X-QPS-Live-Allotted' in headers:
            qps_live_allotted = int(headers.get('X-QPS-Live-Allotted'))
        if 'X-QPS-Live-Current' in headers:
            qps_live_current = int(headers.get('X-QPS-Live-Current'))
        if 'X-QPS-Demo-Allotted' in headers:
            qps_demo_allotted = int(headers.get('X-QPS-Demo-Allotted'))
        if 'X-QPS-Demo-Current' in headers:
            qps_demo_current = int(headers.get('X-QPS-Demo-Current'))

        # Handle Demo usage allowance
        if 'X-Demo-Usage-Allotted' in headers:
            demo_usage_allotted = int(headers.get('X-Demo-Usage-Allotted'))
        if 'X-Demo-Usage-Current' in headers:
            demo_usage_current = int(headers.get('X-Demo-Usage-Current'))
        if 'X-Demo-Usage-Expiry' in headers:
            datetime_str = headers.get('X-Demo-Usage-Expiry')
            demo_usage_expiry = datetime.datetime.strptime(datetime_str, time_format).replace(tzinfo=pytz.utc)

        # Handle Package Usage
        if 'X-Package-Allotted' in headers:
            package_allotted = int(headers.get('X-Package-Allotted'))
        if 'X-Package-Current' in headers:
            package_current = int(headers.get('X-Package-Current'))
        if 'X-Package-Expiry' in headers:
            datetime_str = headers.get('X-Package-Expiry')
            package_expiry = datetime.datetime.strptime(datetime_str, time_format).replace(tzinfo=pytz.utc)

        return (quota_allotted, quota_current, quota_reset, qps_allotted, qps_current, qps_live_allotted,
                qps_live_current, qps_demo_allotted, qps_demo_current, demo_usage_allotted,
                demo_usage_current, demo_usage_expiry, package_allotted, package_current, package_expiry)

    def send_async(self, callback, strict_validation=True):
        """Same as send() but in a non-blocking way.
        
        use this method if you want to send the request asynchronously so your 
        program can do other things while waiting for the response.
        
        :param strict_validation: bool. Used by self.validate_query_params.
        :param callback: Callable with the following signature - callback(response=None, error=None).
        
        example:
        
        >>> from piplapis.search import SearchAPIRequest
        >>>
        >>> def my_callback(response=None, error=None):
        ...     print response or error
        ...
        >>> request = SearchAPIRequest('YOURKEY', email='clark.kent@example.com')
        >>> request.send_async(my_callback)
        >>> do_other_things()
        """

        def target():
            try:
                response = self.send(strict_validation)
                callback(response=response)
            except Exception as e:
                callback(error=e)

        threading.Thread(target=target).start()

    def get_base_url(self):
        protocol = "https"
        return self.BASE_URL.format(protocol)


class SearchAPIResponse(Serializable):
    """a response from Pipl's Search API.

    a response contains 4 main data elements:

    - available data summary (piplapis.data.available_data.AvailableData).
      This is a summary of the data available for your search. Please note that
      some available data may not be present in the response due to data package limits.
      The available data contains two sub-elements, basic and premium (if you're on premium,
      basic will be None):
      - basic: shows the data available with a basic coverage plan
      - premium: shows the data available with a premium coverage plan

    - a person (piplapis.data.containers.Person) that is the data object
      representing all the information available for the person you were
      looking for.
      this object will only be returned when our identity-resolution engine is
      convinced that the information is of the person represented by your query.
      obviously, if the query was for "John Smith" there's no way for our
      identity-resolution engine to know which of the hundreds of thousands of
      people named John Smith you were referring to, therefore you can expect
      that the response will not contain a person object.
      on the other hand, if you search by a unique identifier such as email or
      a combination of identifiers that only lead to one person, such as
      "Clark Kent from Smallville, KS, US", you can expect to get
      a response containing a single person object.
   
    - a list of possible persons (piplapis.data.containers.Person). If our identity-resolution
      engine did not find a definite match, you can use this list to further
      drill down using the persons' search_pointer field.

    - a list of sources (piplapis.data.containers.Source). Sources are the breakdown
      of a response's data into its origin - so each source will contain data that came
      from one source (e.g. a facebook profile, a public record, etc).
      Sources may contain strictly data that belongs to the person returned as a
      perfect match (only these are shown if the search contained show_sources=matching),
      or they may belong to possibly related people. In any case, by default API
      responses do not contain sources, and to use them you must pass a value for show_sources.
   
    the response also contains the query as it was interpreted by Pipl. This
    part is useful for verification and debugging, if some query parameters
    were invalid you can see in response.query that they were ignored, you can
    also see how the name/address from your query were parsed in case you
    passed raw_name/raw_address in the query.
    """

    def __init__(self, query=None, person=None, sources=None,
                 possible_persons=None, warnings_=None, http_status_code=None,
                 visible_sources=None, available_sources=None, search_id=None,
                 match_requirements=None, available_data=None, source_category_requirements=None,
                 persons_count=None, *args, **kwargs):
        """
        :param query: A Person object with the query as interpreted by Pipl.
        :param person: A Person object with data about the person in the query.
        :param sources: A list of Source objects with full/partial match to the query.
        :param possible_persons: A list of Person objects, each of these is an
                              expansion of the original query, giving additional
                              query parameters to zoom in on the right person.
        :param warnings_: A list of unicodes. A warning is returned when the query
                    contains a non-critical error and the search can still run.
        :param visible_sources: int, the number of sources in response
        :param available_sources: int, the total number of known sources for this search
        :param search_id: str or unicode, a unique ID which identifies this search. Useful for debugging.
        :param available_data: an AvailableData object, showing the data available for your query.
        :param match_requirements: str or unicode. Shows how Pipl interpreted your match_requirements criteria.
        :param source_category_requirements: str or unicode. Shows how Pipl interpreted your
                                             source_category_requirements criteria.
         :param persons_count: int. The number of persons in this response.
        """
        self.query = query
        self.person = person
        self.sources = sources or []
        self.possible_persons = possible_persons or []
        self.warnings = warnings_ or []
        self.http_status_code = http_status_code
        self.visible_sources = visible_sources
        self.available_sources = available_sources
        self.search_id = search_id
        self.available_data = available_data
        self.match_requirements = match_requirements
        self.source_category_requirements = source_category_requirements
        self.persons_count = persons_count
        if not self.persons_count:
            self.persons_count = 1 if self.person is not None else len(self.possible_persons)
        self.raw_json = None

        # Rate limiting data
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
        self.package_allotted = None  # The total number of matches defined on the key.
        self.package_current = None  # The number of used matches.
        self.package_expiry = None  # The date and time when the key and the remaining matches will expire.

    @property
    def matching_sources(self):
        """Sources that match the person from the query.
        Note that the meaning of "match the person from the query" means "Pipl 
        is convinced that these sources hold data about the person you're 
        looking for". 
        Essentially, these are the sources that make up the Person object.
        """
        return [source for source in self.sources if source.match == 1.]

    def group_sources(self, key_function):
        """Return a dict with the sources grouped by the key returned by 
        `key_function`.

        :param key_function: function, takes a source and returns the value from the source to
        group by (see examples in the group_sources_by_* methods below).

        :return dict, a key in this dict is a key returned by
        `key_function` and the value is a list of all the sources with this key.
        """
        sorted_sources = sorted(self.sources, key=key_function)
        grouped_sources = itertools.groupby(sorted_sources, key=key_function)
        return dict([(key, list(group)) for key, group in grouped_sources])

    def group_sources_by_domain(self):
        """Return the sources grouped by the domain they came from.
        
        :return dict, a key in this dict is a domain
        and the value is a list of all the sources with this domain.
        
        """
        key_function = lambda source: source.domain or ''
        return self.group_sources(key_function)

    def group_sources_by_category(self):
        """Return the sources grouped by their category. 
        
        :return dict, a key in this dict is a category
        and the value is a list of all the sources with this category.
        
        """
        key_function = lambda source: source.category or ''
        return self.group_sources(key_function)

    def group_sources_by_match(self):
        """Return the sources grouped by their match attribute.

        :return dict, a key in this dict is a match
        float and the value is a list of all the sources with this
        match value.

        """
        key_function = lambda source: source.match or 0
        return self.group_sources(key_function)

    @classmethod
    def from_json(cls, json_str):
        """
        We override this method in SearchAPIResponse so that
        :param json_str:
        :return:
        """
        d = json.loads(json_str)
        obj = cls.from_dict(d)
        obj.raw_json = json_str
        return obj

    @classmethod
    def from_dict(cls, d):
        """Transform the dict to a response object and return the response.
        :param d: the API response dictionary
        """
        http_status_code = d.get('@http_status_code')
        visible_sources = d.get('@visible_sources')
        available_sources = d.get('@available_sources')
        warnings_ = d.get('warnings', [])
        search_id = d.get('@search_id')
        persons_count = d.get('@persons_count')

        match_requirements = d.get('match_requirements')
        source_category_requirements = d.get('source_category_requirements')

        available_data = d.get('available_data') or None
        if available_data is not None:
            available_data = AvailableData.from_dict(available_data)

        query = d.get('query') or None
        if query is not None:
            query = Person.from_dict(query)

        person = d.get('person') or None
        if person is not None:
            person = Person.from_dict(person)
        sources = d.get('sources')
        if sources:
            sources = [Source.from_dict(source) for source in sources]
        possible_persons = [Person.from_dict(x) for x in d.get('possible_persons', [])]
        return cls(query=query, person=person, sources=sources,
                   possible_persons=possible_persons, warnings_=warnings_,
                   http_status_code=http_status_code, visible_sources=visible_sources,
                   available_sources=available_sources, search_id=search_id,
                   match_requirements=match_requirements, available_data=available_data,
                   source_category_requirements=source_category_requirements,
                   persons_count=persons_count)

    def to_dict(self):
        """Return a dict representation of the response."""
        d = {}
        if self.http_status_code:
            d['@http_status_code'] = self.http_status_code
        if self.visible_sources:
            d['@visible_sources'] = self.visible_sources
        if self.available_sources:
            d['@available_sources'] = self.available_sources
        if self.search_id:
            d['@search_id'] = self.search_id
        if self.persons_count:
            d['@persons_count'] = self.persons_count
        if self.warnings:
            d['warnings'] = self.warnings
        if self.match_requirements:
            d['match_requirements'] = self.match_requirements
        if self.available_data is not None:
            d['available_data'] = self.available_data.to_dict()
        if self.query is not None:
            d['query'] = self.query.to_dict()
        if self.person is not None:
            d['person'] = self.person.to_dict()
        if self.sources:
            d['sources'] = [source.to_dict() for source in self.sources]
        if self.possible_persons:
            d['possible_persons'] = [person.to_dict() for person in self.possible_persons]
        return d

    @property
    def gender(self):
        """
        A shortcut method to get the result's person's gender.
        return Gender
        """
        return self.person.gender if self.person else None

    @property
    def dob(self):
        """
        A shortcut method to get the result's person's age.
        return DOB
        """
        return self.person.dob if self.person else None

    @property
    def job(self):
        """
        A shortcut method to get the result's person's job.
        return Job
        """
        return self.person.jobs[0] if self.person and len(self.person.jobs) > 0 else None

    @property
    def address(self):
        """
        A shortcut method to get the result's person's address.
        return Address
        """
        return self.person.addresses[0] if self.person and len(self.person.addresses) > 0 else None

    @property
    def education(self):
        """
        A shortcut method to get the result's person's education.
        return Education
        """
        return self.person.educations[0] if self.person and len(self.person.educations) > 0 else None

    @property
    def language(self):
        """
        A shortcut method to get the result's person's spoken language.
        return Language
        """
        return self.person.languages[0] if self.person and len(self.person.languages) > 0 else None

    @property
    def ethnicity(self):
        """
        A shortcut method to get the result's person's ethnicity.
        return Ethnicity
        """
        return self.person.ethnicities[0] if self.person and len(self.person.ethnicities) > 0 else None

    @property
    def origin_country(self):
        """
        A shortcut method to get the result's person's origin country.
        return OriginCountry
        """
        return self.person.origin_countries[0] if self.person and len(self.person.origin_countries) > 0 else None

    @property
    def phone(self):
        """
        A shortcut method to get the result's person's phone.
        return Phone
        """
        return self.person.phones[0] if self.person and len(self.person.phones) > 0 else None

    @property
    def email(self):
        """
        A shortcut method to get the result's person's email.
        return Email
        """
        return self.person.emails[0] if self.person and len(self.person.emails) > 0 else None

    @property
    def name(self):
        """
        A shortcut method to get the result's person's name.
        return Name
        """
        return self.person.names[0] if self.person and len(self.person.names) > 0 else None

    @property
    def image(self):
        """
        A shortcut method to get the result's person's image.
        return Image
        """
        return self.person.images[0] if self.person and len(self.person.images) > 0 else None

    @property
    def url(self):
        """
        A shortcut method to get the result's person's url.
        return URL
        """
        return self.person.urls[0] if self.person and len(self.person.urls) > 0 else None

    @property
    def username(self):
        """
        A shortcut method to get the result's person's username.
        return Username
        """
        return self.person.usernames[0] if self.person and len(self.person.usernames) > 0 else None

    @property
    def user_id(self):
        """
        A shortcut method to get the result's person's user_id.
        return UserID
        """
        return self.person.user_ids[0] if self.person and len(self.person.user_ids) > 0 else None

    @property
    def relationship(self):
        """
        A shortcut method to get the result's person's most prominent relationship.
        return Relationship
        """
        return self.person.relationships[0] if self.person and len(self.person.relationships) > 0 else None

    def add_quota_throttle_data(self, *args, **kwargs):
        logger.warn("SearchAPIResponse.add_quota_throttle_data is deprecated")
        return self._add_rate_limiting_headers(*args, **kwargs)

    def _add_rate_limiting_headers(self, quota_allotted=None, quota_current=None, quota_reset=None, qps_allotted=None,
                                   qps_current=None, qps_live_allotted=None, qps_live_current=None,
                                   qps_demo_allotted=None, qps_demo_current=None, demo_usage_allotted=None,
                                   demo_usage_current=None, demo_usage_expiry=None, package_allotted=None,
                                   package_current=None, package_expiry=None):
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
        self.package_allotted = package_allotted
        self.package_current = package_current
        self.package_expiry = package_expiry


class SearchAPIError(APIError):
    """an exception raised when the response from the search API contains an
    error."""

    pass