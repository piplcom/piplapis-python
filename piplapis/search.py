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
import urllib
import urllib2
import itertools
import threading

import piplapis
from piplapis.error import APIError
from piplapis.data import *
from piplapis.data.utils import Serializable


class SearchAPIRequest(object):
    """A request to Pipl's Search API.
    
    Building the request from the query parameters can be done in two ways:
    
    Option 1 - directly and quickly (for simple requests with only few 
               parameters):
            
    >>> from piplapis.search import SearchAPIRequest
    >>> request = SearchAPIRequest(api_key='samplekey', 
                                   email='clark.kent@example.com')
    >>> response = request.send()
    
    Option 2 - using the data-model (useful for more complex queries; for 
               example, when there are multiple parameters of the same type 
               such as few phones or a few addresses or when you'd like to use 
               information beyond the usual identifiers such as name or email, 
               information like education, job, relationships etc):
            
    >>> from piplapis.search import SearchAPIRequest
    >>> from piplapis.data import Person, Name, Address, Job
    >>> fields = [Name(first='Clark', last='Kent'),
                  Address(country='US', state='KS', city='Smallville'),
                  Address(country='US', state='KS', city='Metropolis'),
                  Job(title='Field Reporter')]
    >>> request = SearchAPIRequest(api_key='samplekey',
                                   person=Person(fields=fields))
    >>> response = request.send()

    Sending the request and getting the response is very simple and can be done
    by either making a blocking call to request.send() or by making 
    a non-blocking call to request.send_async(callback) which sends the request 
    asynchronously.
    
    You can also set various request flags:
    minimum_probability - a float between 0 and 1, to define what statistical confidence you need for inferred data.
    show_sources - string, either "all", "matching". If not set, no sources will be shown.
        "all" - all sources will be shown.
        "matching" - only sources belonging to a matching person will be shown.
    hide_sponsored - boolean (default False), whether to hide sponsored results.
    minimum_match - a float between 0 and 1, to define the minimum match under which possible persons will not be returned.
    that may be the person you're looking for)
    live_feeds - boolean (default True), whether to use live data feeds. Can be turned off 
    for performance.
    """

    HEADERS = {'User-Agent': 'piplapis/python/%s' % piplapis.__version__}
    BASE_URL = '{}://api.pipl.com/search/v4/?'

    # The following are default settings for all request objects
    # You can set them once instead of passing them to the constructor every time
    default_api_key = 'sample_key'
    default_use_https = False
    default_minimum_probability = None
    default_show_sources = None
    default_minimum_match = None
    default_hide_sponsored = None
    default_live_feeds = None

    @classmethod
    def set_default_settings(cls, api_key=None, minimum_probability=None, show_sources=None,
                             minimum_match=None, hide_sponsored=None, live_feeds=None, use_https=False):
        cls.default_api_key = api_key
        cls.default_minimum_probability = minimum_probability
        cls.default_show_sources = show_sources
        cls.default_minimum_match = minimum_match
        cls.default_hide_sponsored = hide_sponsored
        cls.default_live_feeds = live_feeds
        cls.default_use_https = use_https

    def __init__(self, api_key=None, first_name=None, middle_name=None,
                 last_name=None, raw_name=None, email=None, phone=None, country_code=None,
                 raw_phone=None, username=None, country=None, state=None, city=None,
                 raw_address=None, from_age=None, to_age=None, person=None,
                 search_pointer=None, minimum_probability=None, show_sources=None,
                 minimum_match=None, hide_sponsored=None, live_feeds=None, use_https=None):
        """Initiate a new request object with given query params.
        
        Each request must have at least one searchable parameter, meaning 
        a name (at least first and last name), email, phone or username. 
        Multiple query params are possible (for example querying by both email 
        and phone of the person).
        
        Args:
        
        api_key -- str, a valid API key (use "samplekey" for experimenting).
                   Note that you can set a default API key 
                   (piplapis.search.default_api_key = '<your_key>') instead of 
                   passing it to each request object. 
        first_name -- unicode, minimum 2 chars.
        middle_name -- unicode. 
        last_name -- unicode, minimum 2 chars.
        raw_name -- unicode, an unparsed name containing at least a first name 
                    and a last name.
        email -- unicode.
        phone -- int/long. A national phone with no formatting.
        country_code -- int. The phone country code
        raw_phone -- string. A phone to be sent as-is, will be parsed by Pipl.
        username -- unicode, minimum 4 chars.
        country -- unicode, a 2 letter country code from:
                   http://en.wikipedia.org/wiki/ISO_3166-2
        state -- unicode, a state code from:
                 http://en.wikipedia.org/wiki/ISO_3166-2%3AUS
                 http://en.wikipedia.org/wiki/ISO_3166-2%3ACA
        city -- unicode.
        raw_address -- unicode, an unparsed address.
        from_age -- int.
        to_age -- int.
        person -- A Person object (available at piplapis.data.Person).
                  The person can contain every field allowed by the data-model
                  (see piplapis.data.fields) and can hold multiple fields of
                  the same type (for example: two emails, three addresses etc.)
        search_pointer -- str, sending a search pointer of a possible person will retrieve 
                          more data related to this person.
        minimum_probability -- float (0-1). The minimum required confidence for inferred data.
        show_sources -- str, one of "matching"/"all". "all" will show all sources, "matching"
                        only those of the matching person. If not set, no sources will be shown.
        minimum_match -- float (0-1). The minimum required match under which possible persons will not be returned.
        live_feeds -- bool, default True. Whether to use live feeds. Only relevant in plans that include
                      live feeds. Can be set to False for performance.
        hide_sponsored -- bool, default False. Whether to hide sponsored results.
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
        if country or state or city:
            address = Address(country=country, state=state, city=city)
            person.add_fields([address])
        if raw_address:
            person.add_fields([Address(raw=raw_address)])
        if from_age is not None or to_age is not None:
            dob = DOB.from_age_range(from_age or 0, to_age or 1000)
            person.add_fields([dob])

        person.search_pointer = search_pointer
        self.person = person

        self.api_key = api_key or self.default_api_key
        self.show_sources = show_sources or self.default_show_sources
        self.live_feeds = live_feeds or self.default_live_feeds
        self.minimum_match = minimum_match or self.default_minimum_match
        self.minimum_probability = minimum_probability or self.default_minimum_probability
        self.hide_sponsored = hide_sponsored or self.default_hide_sponsored
        self.use_https = use_https

    def validate_query_params(self, strict=True):
        """Check if the request is valid and can be sent, raise ValueError if 
        not.
        
        `strict` is a boolean argument that defaults to True which means an 
        exception is raised on every invalid query parameter, if set to False
        an exception is raised only when the search request cannot be performed
        because required query params are missing.
        
        """
        if not self.api_key:
            raise ValueError('API key is missing')
        if strict and self.minimum_match and (type(self.minimum_match) is not float or
                                                      self.minimum_match > 1 or self.minimum_match < 0):
            raise ValueError('minimum_match should be a float between 0 and 1')
        if strict and self.hide_sponsored is not None and type(self.hide_sponsored) is not bool:
            raise ValueError('hide_sponsored should be a boolean')
        if strict and self.live_feeds is not None and type(self.live_feeds) is not bool:
            raise ValueError('live_feeds should be a boolean')
        if strict and self.show_sources not in ("all", "matching", "false", False, None):
            raise ValueError('show_sources has a wrong value. Should be "matching", "all", or None')
        if strict and self.minimum_probability and (type(self.minimum_probability) is not float or
                                                            self.minimum_probability > 1 or self.minimum_probability < 0):
            raise ValueError('minimum_probability should be a float between 0 and 1')
        if not self.person.is_searchable:
            raise ValueError('No valid name/username/phone/email or search pointer in request')
        if strict and self.person.unsearchable_fields:
            raise ValueError('Some fields are unsearchable: %s'
                             % self.person.unsearchable_fields)

    @property
    def url(self):
        """The URL of the request (str)."""
        query = self.get_search_query()
        return self.get_base_url() + urllib.urlencode(query, doseq=True)

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
        if self.hide_sponsored is not None:
            query['hide_sponsored'] = self.hide_sponsored
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
        
        `strict_vailidation` is a bool argument that's passed to the 
        validate_query_params method.
        
        raises ValueError (raised from validate_query_params), 
        httpError/URLError and SearchAPIError (when the response is returned 
        but contains an error).
        
        example:
        
        >>> from piplapis.search import SearchAPIRequest, SearchAPIError
        >>> request = SearchAPIRequest('samplekey', email='clark.kent@example.com')
        >>> try:
        ...     response = request.send()
        ... except SearchAPIError as e:
        ...     print e.http_status_code, e
        
        """
        self.validate_query_params(strict=strict_validation)

        query = self.get_search_query()
        request = urllib2.Request(url=self.get_base_url(), data=urllib.urlencode(query, True),
                                  headers=SearchAPIRequest.HEADERS)
        try:
            json_response = urllib2.urlopen(request).read()
        except urllib2.HTTPError as e:
            json_error = e.read()
            if not json_error:
                raise e
            try:
                raise SearchAPIError.from_json(json_error)
            except ValueError:
                raise e
        return SearchAPIResponse.from_json(json_response)

    def send_async(self, callback, strict_validation=True):
        """Same as send() but in a non-blocking way.
        
        use this method if you want to send the request asynchronously so your 
        program can do other things while waiting for the response.
        
        `callback` is a function (or other callable) with the following 
        signature:
        callback(response=None, error=None)
        
        example:
        
        >>> from piplapis.search import SearchAPIRequest
        >>>
        >>> def my_callback(response=None, error=None):
        ...     print response or error
        ...
        >>> request = SearchAPIRequest('samplekey', email='clark.kent@example.com')
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
        protocol = "https" if self.use_https or (self.use_https is None and self.default_use_https) else "http"
        return self.BASE_URL.format(protocol)


class SearchAPIResponse(Serializable):
    """a response from Pipl's Search API.

    a response comprises the three things returned as a result to your query:

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
      "eric Cartman, Age 22, From South Park, CO, US", you can expect to get
      a response containing a single person object.
   
    - a list of possible persons (piplapis.data.containers.Person). If our identity-resolution
      engine did not find a definite match, you can use this list to further
      drill down using the persons' search_pointer field.

    - a list of sources (piplapis.data.containers.Source) that fully/partially
      match the person from your query, if the query was for "Eric Cartman from
      colorado US" the response might also contain sources of "Eric Cartman
      from US" (without Colorado), if you need to differentiate between sources
      with full match to the query and partial match or if you want to get a
      score on how likely is that source to be related to the person you are
      searching please refer to the source's "match" field.
   
    the response also contains the query as it was interpreted by Pipl. This
    part is useful for verification and debugging, if some query parameters
    were invalid you can see in response.query that they were ignored, you can
    also see how the name/address from your query were parsed in case you
    passed raw_name/raw_address in the query.
    """

    def __init__(self, query=None, person=None, sources=None,
                 possible_persons=None, warnings_=None, http_status_code=None,
                 visible_sources=None, available_sources=None, search_id=None):
        """Args:
        
        query -- A Person object with the query as interpreted by Pipl.
        person -- A Person object with data about the person in the query.
        sources -- A list of Source objects with full/partial match to the 
                   query.
        possible_persons -- A list of Person objects, each of these is an 
                              expansion of the original query, giving additional
                              query parameters to zoom in on the right person.
        warnings_ -- A list of unicodes. A warning is returned when the query 
                    contains a non-critical error and the search can still run.
        visible_sources -- the number of sources in response
        available_sources -- the total number of known sources for this search
        search_id -- a unique ID which identifies this search. Useful for debugging.
                    
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
        
        `key_function` takes a source and returns the value from the source to
        group by (see examples in the group_sources_by_* methods below).
        
        the return value is a dict, a key in this dict is a key returned by
        `key_function` and the value is a list of all the sources with this key.
        
        """
        sorted_sources = sorted(self.sources, key=key_function)
        grouped_sources = itertools.groupby(sorted_sources, key=key_function)
        return dict([(key, list(group)) for key, group in grouped_sources])

    def group_sources_by_domain(self):
        """Return the sources grouped by the domain they came from.
        
        the return value is a dict, a key in this dict is a domain
        and the value is a list of all the sources with this domain.
        
        """
        key_function = lambda source: source.domain
        return self.group_sources(key_function)

    def group_sources_by_category(self):
        """Return the sources grouped by their category. 
        
        the return value is a dict, a key in this dict is a category
        and the value is a list of all the sources with this category.
        
        """
        key_function = lambda source: source.category
        return self.group_sources(key_function)

    def group_sources_by_match(self):
        """Return the sources grouped by their match attribute.

        the return value is a dict, a key in this dict is a match
        float and the value is a list of all the sources with this
        match value.

        """
        key_function = lambda source: source.match
        return self.group_sources(key_function)

    @staticmethod
    def from_dict(d):
        """Transform the dict to a response object and return the response."""
        http_status_code = d.get('@http_status_code')
        visible_sources = d.get('@visible_sources')
        available_sources = d.get('@available_sources')
        warnings_ = d.get('warnings', [])
        search_id = d.get('@search_id')
        query = d.get('query') or None
        if query:
            query = Person.from_dict(query)
        person = d.get('person') or None
        if person:
            person = Person.from_dict(person)
        sources = d.get('sources')
        if sources:
            sources = [Source.from_dict(source) for source in sources]
        possible_persons = [Person.from_dict(x) for x in d.get('possible_persons', [])]
        return SearchAPIResponse(query=query, person=person, sources=sources,
                                 possible_persons=possible_persons,
                                 warnings_=warnings_, http_status_code=http_status_code,
                                 visible_sources=visible_sources, available_sources=available_sources,
                                 search_id=search_id)

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
        if self.warnings:
            d['warnings'] = self.warnings
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


class SearchAPIError(APIError):
    """an exception raised when the response from the search API contains an
    error."""

    pass
