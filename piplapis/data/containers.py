import itertools

from piplapis.data.fields import *
from piplapis.data.utils import *

__all__ = ['Source', 'Person', 'Relationship']


class FieldsContainer(object):
    """The base class of Source, Person and Relationship, made only for inheritance.
    Do not use this class directly.
    """
    class_container = NotImplemented  # Implement in subclass
    singular_fields = NotImplemented  # Implement in subclass

    def __init__(self, fields=None, *args, **kwargs):
        """`fields` is an iterable of field objects from
        piplapis.data.fields."""
        self.names = []
        self.addresses = []
        self.phones = []
        self.emails = []
        self.jobs = []
        self.educations = []
        self.images = []
        self.usernames = []
        self.user_ids = []
        self.languages = []
        self.ethnicities = []
        self.origin_countries = []
        self.urls = []
        self.relationships = []
        self.tags = []
        self.dob = None
        self.gender = None
        self.add_fields(fields or [])

    def add_fields(self, fields):
        """Add the fields to their corresponding container.
        
        :param fields: iterable of field objects from piplapis.data.fields.
        """
        for field in fields:
            cls = field.__class__
            if cls in self.class_container.keys():
                container = self.class_container[cls]
                getattr(self, container).append(field)
            elif cls in self.singular_fields.keys():
                container = self.singular_fields[cls]
                setattr(self, container, field)
            else:
                raise ValueError('Object of type %s is an invalid field' % cls)

    @property
    def all_fields(self):
        """A list with all the fields contained in this object."""
        multiple = [field for container in self.class_container.values()
                    for field in getattr(self, container)]
        single = [getattr(self, field_name) for field_name in self.singular_fields.values()
                  if getattr(self, field_name)]
        return multiple + single

    @classmethod
    def fields_from_dict(cls, d):
        """Load the fields from the dict, return a list with all the fields.
        :param d: dict, the dictionary to load object from.
        """
        class_container = cls.class_container
        fields = [field_cls.from_dict(field_dict)
                  for field_cls, container in class_container.items()
                  for field_dict in d.get(container, [])]
        for field_cls, attr_name in cls.singular_fields.items():
            if attr_name in d:
                fields.append(field_cls.from_dict(d[attr_name]))
        return fields

    def fields_to_dict(self):
        """Transform the object to a dict and return the dict."""
        d = {}
        for container in self.class_container.values():
            fields = getattr(self, container)
            if fields:
                d[container] = [field.to_dict() for field in fields]
        for attr_name in self.singular_fields.values():
            if getattr(self, attr_name):
                d[attr_name] = getattr(self, attr_name).to_dict()
        return d


class Relationship(Serializable, FieldsContainer):
    """Another person related to this person."""

    class_container = {
        Name: 'names',
        Address: 'addresses',
        Phone: 'phones',
        Email: 'emails',
        Job: 'jobs',
        Education: 'educations',
        Image: 'images',
        Username: 'usernames',
        UserID: 'user_ids',
        URL: 'urls',
        Ethnicity: 'ethnicities',
        OriginCountry: 'origin_countries',
        Language: 'languages'
    }

    singular_fields = {
        Gender: 'gender',
        DOB: 'dob'
    }

    attributes = ('type', 'subtype')
    types_set = set(['friend', 'family', 'work', 'other'])

    def __init__(self, fields=None, type_=None, subtype=None,
                 valid_since=None, inferred=None, *args, **kwargs):
        """`fields` is a list of fields (plapis.data.fields.Field subclasses)
        
        `type_` and `subtype` should both be unicode objects or utf8 encoded 
        strs (will be decoded automatically).
        
        `type_` is one of Relationship.types_set.
        
        `subtype` is not restricted to a specific list of possible values (for 
        example, if type_ is "family" then subtype can be "Father", "Mother", 
        "Son" and many other things).
        
        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.
        
        """
        super(Relationship, self).__init__(fields, *args, **kwargs)
        self.type = type_
        self.subtype = subtype
        self.valid_since = valid_since
        self.inferred = inferred

    @classmethod
    def from_dict(cls, d):
        """Transform the dict to a relationship object and return the relationship.
        :param d: dict, the dictionary to create a Relationship from.
        """
        fields = cls.fields_from_dict(d)
        ins = cls(fields=fields)
        if "@type" in d:
            ins.type = d['@type']
        if "@subtype" in d:
            ins.subtype = d['@subtype']
        if "@valid_since" in d and d['@valid_since']:
            ins.valid_since = str_to_datetime(d['@valid_since'])
        if "@inferred" in d:
            ins.inferred = d['@inferred']
        return ins

    def to_dict(self):
        """Return a dict representation of the relationship."""
        d = {}
        if self.type is not None:
            d['@type'] = self.type
        if self.subtype:
            d['@subtype'] = self.subtype
        if self.inferred:
            d['@inferred'] = self.inferred
        if self.valid_since is not None:
            d['@valid_since'] = datetime_to_str(self.valid_since)
        d.update(self.fields_to_dict())
        return d

    def __str__(self):
        return str(self.names[0]) if self.names and len(self.names) > 0 else ""


class Source(Serializable, FieldsContainer):
    """A source objects holds the data retrieved from a specific source.

    Every source object is based on the URL of the 
    page where the data is available, and the data itself that comes as field
    objects (Name, Address, Email etc. see piplapis.data.fields).

    Each type of field has its own container (note that Source is a subclass 
    of FieldsContainer).
    For example:

    >>> from piplapis.data import Source, Email, Phone
    >>> fields = [Email(address='clark.kent@example.com'), Phone(number=999888777)]
    >>> source = Source(fields=fields)
    >>> source.emails
    [Email(address=u'clark.kent@example.com')]
    >>> source.phones
    [Phone(number=999888777)]

    Sources come as results for a query and therefore they have attributes that
    indicate if and how much they match the query. They also have a validity 
    timestamp available as an attribute.

    """

    class_container = {
        Name: 'names',
        Address: 'addresses',
        Phone: 'phones',
        Email: 'emails',
        Job: 'jobs',
        Education: 'educations',
        Image: 'images',
        Username: 'usernames',
        UserID: 'user_ids',
        URL: 'urls',
        Relationship: 'relationships',
        Ethnicity: 'ethnicities',
        OriginCountry: 'origin_countries',
        Language: 'languages',
        Tag: 'tags'
    }

    singular_fields = {
        Gender: 'gender',
        DOB: 'dob'
    }

    def __init__(self, fields=None, match=None, name=None, category=None, origin_url=None,
                 sponsored=None, domain=None, source_id=None, person_id=None, premium=None,
                 valid_since=None, *args, **kwargs):
        """Extend FieldsContainer.__init__ and set the source's attributes.

        Args:

        fields -- An iterable of fields (from piplapis.data.fields).
        match -- A float between 0.0 and 1.0 that indicates how
                              likely it is that this source holds data about
                              the person from the query.
                              Higher value means higher likelihood, value
                              of 1.0 means "this is definitely him".
                              This value is based on Pipl's statistical
                              algorithm that takes into account many parameters
                              like the popularity of the name/address (if there
                              was a name/address in the query) etc.
        name -- A string, the source name
        category -- A string, the source category
        origin_url -- A string, the URL where Pipl's crawler found this data
        sponsored -- A boolean, whether the source is a sponsored result or not
        domain -- A string, the domain of this source
        person_id -- A string, the person's unique ID
        source_id -- A string, the source ID
        premium -- A boolean, whether this is a premium source
        valid_since -- A datetime.datetime object, this is the first time
                       Pipl's crawlers saw this source.

        """
        FieldsContainer.__init__(self, fields, *args, **kwargs)
        self.match = match
        self.valid_since = valid_since
        self.name = name
        self.category = category
        self.origin_url = origin_url
        self.domain = domain
        self.sponsored = sponsored
        self.source_id = source_id
        self.person_id = person_id
        self.premium = premium

    @classmethod
    def from_dict(cls, d):
        """Transform the dict to a source object and return the source.
        :param d: dict, the dictionary to create a Source from.
        """
        match = d.get('@match')
        name = d.get('@name')
        category = d.get('@category')
        origin_url = d.get('@origin_url')
        domain = d.get('@domain')
        sponsored = d.get('@sponsored')
        valid_since = d.get('@valid_since')
        person_id = d.get('@person_id')
        premium = d.get('@premium')
        source_id = d.get('@id')
        if valid_since:
            valid_since = str_to_datetime(valid_since)
        fields = cls.fields_from_dict(d)
        return cls(fields=fields, match=match, name=name, category=category,
                   origin_url=origin_url, domain=domain, sponsored=sponsored,
                   valid_since=valid_since, source_id=source_id, premium=premium, person_id=person_id)

    def to_dict(self):
        """Return a dict representation of the source."""
        d = {}
        if self.name is not None:
            d['@name'] = self.name
        if self.category is not None:
            d['@category'] = self.category
        if self.origin_url is not None:
            d['@origin_url'] = self.origin_url
        if self.domain is not None:
            d['@domain'] = self.domain
        if self.sponsored is not None:
            d['@sponsored'] = self.sponsored
        if self.match is not None:
            d['@match'] = self.match
        if self.person_id is not None:
            d['@person_id'] = self.person_id
        if self.valid_since is not None:
            d['@valid_since'] = datetime_to_str(self.valid_since)
        if self.premium:
            d['@premium'] = self.premium
        if self.source_id:
            d['@id'] = self.source_id
        d.update(self.fields_to_dict())
        return d


class Person(Serializable, FieldsContainer):
    """A Person object is all the data available on an individual.
    
    The Person object is essentially very similar in its structure to the 
    Source object, the main difference is that data about an individual can 
    come from multiple sources.
    
    The person's data comes as field objects (Name, Address, Email etc. see 
    piplapis.data.fields).
    Each type of field has its on container (note that Person is a subclass 
    of FieldsContainer).
    For example:
 
    >>> from piplapis.data import Person, Email, Phone
    >>> fields = [Email(address='clark.kent@example.com'), Phone(number=999888777)]
    >>> person = Person(fields=fields)
    >>> person.emails
    [Email(address=u'clark.kent@example.com')]
    >>> person.phones
    [Phone(number=999888777)]

    Note that a person object is used in the Search API in two ways:
    - It might come back as a result for a query (see SearchResponse).
    - It's possible to build a person object with all the information you
      already have about the person you're looking for and send this object as
      the query (see SearchRequest).

    """

    class_container = {
        Name: 'names',
        Address: 'addresses',
        Phone: 'phones',
        Email: 'emails',
        Job: 'jobs',
        Education: 'educations',
        Image: 'images',
        Username: 'usernames',
        UserID: 'user_ids',
        URL: 'urls',
        Relationship: 'relationships',
        Ethnicity: 'ethnicities',
        OriginCountry: 'origin_countries',
        Language: 'languages'
    }

    singular_fields = {
        Gender: 'gender',
        DOB: 'dob'
    }

    def __init__(self, fields=None, *args, **kwargs):
        """Extend FieldsContainer.__init__ 
        
        Args:
        fields -- An iterable of fields (from piplapis.data.fields).
        """

        FieldsContainer.__init__(self, fields, *args, **kwargs)
        self.person_id = None
        self.search_pointer = None
        self.match = None
        self.inferred = None

    @property
    def is_searchable(self):
        """A bool value that indicates whether the person has enough data and
        can be sent as a query to the API."""
        filter_func = lambda field: field.is_searchable
        return bool(self.search_pointer or
                    list(filter(filter_func, self.names)) or
                    list(filter(filter_func, self.urls)) or
                    list(filter(lambda x: x.is_sole_searchable, self.addresses)) or
                    list(filter(filter_func, self.user_ids)) or
                    list(filter(filter_func, self.emails)) or
                    list(filter(filter_func, self.phones)) or
                    list(filter(filter_func, self.usernames)))

    @property
    def unsearchable_fields(self):
        """A list of all the fields that can't be searched by.
        
        For example: names/usernames that are too short, emails that are 
        invalid etc.
        
        """
        filter_func = lambda field: not field.is_searchable
        return list(itertools.chain(filter(filter_func, self.names),
                                    filter(filter_func, self.emails),
                                    filter(filter_func, self.phones),
                                    filter(filter_func, self.usernames),
                                    filter(filter_func, self.user_ids),
                                    filter(filter_func, self.urls),
                                    filter(filter_func, self.addresses),
                                    filter(filter_func, [x for x in [self.dob] if x])))

    @classmethod
    def from_dict(cls, d):
        """Transform the dict to a person object and return the person.
        :param d: dict, the dictionary to create a Person from.
        """
        fields = cls.fields_from_dict(d)
        ins = cls(fields=fields)
        if "@id" in d:
            ins.person_id = d['@id']
        if "@search_pointer" in d:
            ins.search_pointer = d['@search_pointer']
        if "@match" in d:
            ins.match = d['@match']
        if "@inferred" in d:
            ins.inferred = d['@inferred']
        return ins

    def to_dict(self):
        """Return a dict representation of the person."""
        d = {}
        if self.person_id is not None:
            d['@id'] = self.person_id
        if self.search_pointer is not None:
            d['@search_pointer'] = self.search_pointer
        if self.match is not None:
            d['@match'] = self.match
        if self.inferred is not None:
            d['@inferred'] = self.inferred
        d.update(self.fields_to_dict())
        return d
