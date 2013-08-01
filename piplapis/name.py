"""Python wrapper for easily making calls to Pipl's Name API.

Pipl's Name API provides useful utilities for applications that need to work
with people names, the utilities include:
- Parsing a raw name into prefix/first-name/middle-name/last-name/suffix. 
- Getting the gender that's most common for people with the name.
- Getting possible nicknames of the name.
- Getting possible full-names of the name (in case the name is a nick).
- Getting different spelling options of the name.
- Translating the name to different languages.
- Getting the list of most common locations for people with this name.
- Getting the list of most common ages for people with this name.
- Getting an estimated number of people in the world with this name.

The classes contained in this module are:
- NameAPIRequest -- Build your request and send it.
- NameAPIResponse -- Holds the response from the API in case it contains data.
- NameAPIError -- An exception raised when the API response is an error.

- AltNames -- Used in NameAPIResponse for holding alternative names.
- LocationStats -- Used in NameAPIResponse for holding location data.
- AgeStats -- Used in NameAPIResponse for holding age data.

"""
import urllib
import urllib2

import piplapis
from piplapis.error import APIError
from piplapis.data.utils import Serializable, to_utf8
from piplapis.data.fields import Field, Address, Name


# Default API key value, you can set your key globally in this variable instead 
# of passing it to each request object.
# >>> import piplapis.name
# >>> piplapis.name.default_api_key = '<your_key>'
default_api_key = None


class NameAPIRequest(object):
    
    """A request to Pipl's Name API.
    
    A request is build with a name that can be provided parsed to 
    first/middle/last (in case it's already available to you parsed) 
    or unparsed (and then the API will parse it).
    Note that the name in the request can also be just a first-name or just 
    a last-name.
    
    """
    
    HEADERS = {'User-Agent': 'piplapis/python/%s' % piplapis.__version__}
    BASE_URL = 'http://api.pipl.com/name/v2/json/?'
    # HTTPS is also supported:
    #BASE_URL = 'https://api.pipl.com/name/v2/json/?'
    
    def __init__(self, api_key=None, first_name=None, middle_name=None, 
                 last_name=None, raw_name=None):
        """`api_key` is a valid API key (str), use "samplekey" for 
        experimenting, note that you can set a default API key
        (piplapis.name.default_api_key = '<your_key>') instead of passing it 
        to each request object.
        
        `first_name`, `middle_name`, `last_name`, `raw_name` should all be 
        unicode objects or utf8 encoded strs (will be decoded automatically).
        
        ValueError is raised in case of illegal parameters.
        
        Examples:
        
        >>> from piplapis.name import NameAPIRequest
        >>> request1 = NameAPIRequest(api_key='samplekey', first_name='Eric', 
                                      last_name='Cartman')
        >>> request2 = NameAPIRequest(api_key='samplekey', last_name='Cartman')
        >>> request3 = NameAPIRequest(api_key='samplekey', 
                                      raw_name='Eric Cartman')
        >>> request4 = NameAPIRequest(api_key='samplekey', raw_name='Eric')
        
        """
        if not (api_key or default_api_key):
            raise ValueError('A valid API key is required')
        if not (first_name or middle_name or last_name or raw_name):
            raise ValueError('A name is missing')
        if raw_name and (first_name or middle_name or last_name):
            raise ValueError('Name should be provided raw or parsed, not both')
        self.api_key = api_key
        self.name = Name(first=first_name, middle=middle_name, last=last_name, 
                         raw=raw_name)
    
    @property
    def url(self):
        """The URL of the request (str)."""
        query = {
            'key': self.api_key or default_api_key,
            'first_name': self.name.first or '',
            'middle_name': self.name.middle or '',
            'last_name': self.name.last or '',
            'raw_name': self.name.raw or '',
        }
        query = dict([(k, to_utf8(v)) for k, v in query.iteritems()])
        return NameAPIRequest.BASE_URL + urllib.urlencode(query)
        
    def send(self):
        """Send the request and return the response or raise NameAPIError.
        
        The response is returned as a NameAPIResponse object.

        Raises HttpError/URLError and NameAPIError (when the response is 
        returned but contains an error).
        
        Example:
        
        >>> from piplapis.name import NameAPIRequest, NameAPIError
        >>> request = NameAPIRequest('samplekey', raw_name='Eric Cartman')
        >>> try:
        ...     response = request.send()
        ... except NameAPIError as e:
        ...     print e.http_status_code, e
        
        """
    
        request = urllib2.Request(url=self.url, headers=NameAPIRequest.HEADERS)
        try:
            json_response = urllib2.urlopen(request).read()
        except urllib2.HTTPError as e:
            json_error = e.read()
            if not json_error:
                raise e
            raise NameAPIError.from_json(json_error)
        return NameAPIResponse.from_json(json_response)
    
    
class NameAPIResponse(Serializable):
    
    """A response from Pipl's search API.
    
    A response contains the name from the query (parsed), and when available
    the gender, nicknames, full-names, spelling options, translations, common 
    locations and common ages for the name. It also contains an estimated 
    number of people in the world with this name.
    
    """
    
    def __init__(self, name=None, gender=None, gender_confidence=None, 
                 full_names=None, nicknames=None, spellings=None,
                 translations=None, top_locations=None, top_ages=None, 
                 estimated_world_persons_count=None, warnings_=None):
        """Args:
        
        name -- A piplapis.data.fields.Name object - the name from the query.
        gender -- str, "male" or "female".
        gender_confidence -- float between 0.0 and 1.0, represents how 
                            confidence Pipl is that `gender` is the correct one.
                            (Unisex names will get low confidence score).
        full_names -- An AltNames object.
        nicknames -- An AltNames object.
        spellings -- An AltNames object.
        translations -- A dict of language_code -> AltNames object for this 
                        language.
        top_locations -- A list of LocationStats objects.
        top_ages -- A list of AgeStats objects.
        estimated_world_persons_count -- int, estimated number of people in the 
                                         world with the name from the query.
        warnings_ -- A list of unicodes. A warning is returned when the query 
                     contains a non-critical error.
                     
        """
        self.name = name or Name()
        self.gender = gender
        self.gender_confidence = gender_confidence
        self.full_names = full_names or AltNames()
        self.nicknames = nicknames or AltNames()
        self.spellings = spellings or AltNames()
        self.translations = translations or {}
        self.top_locations = top_locations or []
        self.top_ages = top_ages or []
        self.estimated_world_persons_count = estimated_world_persons_count
        self.warnings = warnings_ or []
        
    @staticmethod
    def from_dict(d):
        """Transform the dict to a response object and return the response."""
        name = Name.from_dict(d.get('name', {}))
        gender, gender_confidence = d.get('gender', [None, None])
        full_names = AltNames.from_dict(d.get('full_names', {}))
        nicknames = AltNames.from_dict(d.get('nicknames', {}))
        spellings = AltNames.from_dict(d.get('spellings', {}))
        translations = dict([(language, AltNames.from_dict(names))
                             for language, names in 
                             d.get('translations', {}).items()])
        top_locations = [LocationStats.from_dict(location_stats)
                         for location_stats in d.get('top_locations', [])]
        top_ages = [AgeStats.from_dict(age_stats)
                    for age_stats in d.get('top_ages', [])]
        world_count = d.get('estimated_world_persons_count')
        warnings_ = d.get('warnings')
        return NameAPIResponse(name=name, gender=gender, 
                               gender_confidence=gender_confidence,
                               full_names=full_names, nicknames=nicknames, 
                               spellings=spellings, translations=translations, 
                               top_locations=top_locations, top_ages=top_ages, 
                               estimated_world_persons_count=world_count,
                               warnings_=warnings_)
        
    def to_dict(self):
        """Return a dict representation of the response."""
        d = {
            'warnings': self.warnings,
            'name': self.name.to_dict(),
            'gender': [self.gender, self.gender_confidence],
            'full_names': self.full_names.to_dict(),
            'nicknames': self.nicknames.to_dict(),
            'spellings': self.spellings.to_dict(),
            'translations': dict([(lng, names.to_dict()) 
                                  for lng, names in self.translations.items()]),
            'top_locations': [location_stats.to_dict() 
                              for location_stats in self.top_locations],
            'top_ages': [age_stats.to_dict() for age_stats in self.top_ages],
            'estimated_world_persons_count': self.estimated_world_persons_count,
        }
        return d


class AltNames(Field):
    
    """Helper class for NameAPIResponse, holds alternate 
    first/middle/last names for a name."""
    
    children = ('first', 'middle', 'last')
    
    def __init__(self, first=None, middle=None, last=None):
        Field.__init__(self)
        self.first = first or []  # list of unicodes
        self.middle = middle or []  # list of unicodes
        self.last = last or []  # list of unicodes


class LocationStats(Address):
    
    """Helper class for NameAPIResponse, holds a location and the estimated 
    percent of people with the name that lives in this location.
    
    Note that this class inherits from Address and therefore has the 
    properties location_stats.country_full, location_stats.state_full and
    location_stats.display.
    
    """
    
    children = ('country', 'state', 'city', 'estimated_percent')
    
    def __init__(self, country=None, state=None, city=None, 
                 estimated_percent=None):
        Address.__init__(self, country=country, state=state, city=city)
        self.estimated_percent = estimated_percent  # 0 <= int <= 100


class AgeStats(Field):
    
    """Helper class for NameAPIResponse, holds an age range and the estimated 
    percent of people with the name that their age is within the range."""
    
    children = ('from_age', 'to_age', 'estimated_percent')
    
    def __init__(self, from_age=None, to_age=None, estimated_percent=None):
        Field.__init__(self)
        self.from_age = from_age  # int
        self.to_age = to_age  # int
        self.estimated_percent = estimated_percent  # 0 <= int <= 100


class NameAPIError(APIError):
    
    """An exception raised when the response from the name API contains an 
    error."""
    
    pass
