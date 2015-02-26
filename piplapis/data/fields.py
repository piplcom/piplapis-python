import re
import datetime
from urllib import urlencode

from piplapis.data.utils import *


__all__ = ['Name', 'Address', 'Phone', 'Email', 'Job', 'Education', 'Image',
           'Username', 'UserID', 'DOB', 'URL', 'Tag',
           'DateRange', 'Ethnicity', 'Language', 'OriginCountry', 'Gender']


class Field(Serializable):
    """Base class of all data fields, made only for inheritance."""

    attributes = ()
    children = ('content',)

    def __init__(self, valid_since=None, inferred=None):
        self.valid_since = valid_since
        self.inferred = inferred

    def __setattr__(self, attr, value):
        """Extend the default object.__setattr___ and make sure that str values 
        are converted to unicode and that assigning to the `type` attribute is 
        only from the allowed values.
        
        Setting an str value for an attribute is impossible, if an str is 
        provided then it must be in utf8 encoding and it will be automatically
        converted to a unicode object.
        
        Example:
        >>> from piplapis.data import Name
        >>> name = Name(first='clark')
        >>> name.first
        u'clark'
        
        """
        if isinstance(value, str):
            try:
                value = value.decode('utf8')
            except UnicodeDecodeError:
                raise ValueError('Tried to assign a non utf8 string to ' + attr)
        if attr == 'type':
            self.validate_type(value)
        object.__setattr__(self, attr, value)

    def __unicode__(self):
        """Return the unicode representation of the object."""
        return unicode(str(self))

    def __str__(self):
        """Return the str representation of the object (encoded with utf8)."""
        if hasattr(self, 'display') and getattr(self, 'display'):
            return self.display.encode('utf8')
        else:
            return ""

    @property
    def display(self):
        return self._display if hasattr(self, '_display') and getattr(self, '_display') else None

    def __repr__(self):
        """Return a representation of the object (a valid value for eval())."""
        attrs = list(self.attributes + self.children)
        attrs.append('valid_since')
        attrs_values = [(attr, getattr(self, attr)) for attr in attrs if not attr.startswith("display")]
        attrs_values = [(attr, value) if attr != 'type' else ('type_', value)
                        for attr, value in attrs_values]
        args = ['%s=%s' % (attr, repr(value))
                for attr, value in attrs_values if value is not None]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(args))

    def __eq__(self, other):
        """Bool, indicates whether `self` and `other` have exactly the same 
        data."""
        return repr(self) == repr(other)

    def validate_type(self, type_):
        """Take an str/unicode `type_` and raise a ValueError if it's not 
        a valid type for the object.
        
        A valid type for a field is a value from the types_set attribute of 
        that field's class. 
        
        """
        if type_ is not None and type_ not in self.types_set:
            raise ValueError('Invalid type for %s:%s' % (self.__class__, type_))

    @classmethod
    def from_dict(cls, d):
        """Transform the dict to a field object and return the field."""
        kwargs = {}
        for key, val in d.iteritems():
            if key.startswith('@'):
                key = key[1:]
            if key == 'type':
                key = 'type_'
            elif key == 'valid_since':
                val = str_to_datetime(val)
            elif key == 'date_range':
                val = DateRange.from_dict(val)
            kwargs[key.encode('ascii')] = val

        return cls(**kwargs)

    def to_dict(self):
        """Return a dict representation of the field."""
        d = {}
        if self.valid_since is not None:
            d['@valid_since'] = datetime_to_str(self.valid_since)
        for attr_list, prefix in [(self.attributes, '@'), (self.children, '')]:
            for attr in attr_list:
                value = getattr(self, attr)
                if isinstance(value, Serializable):
                    value = value.to_dict()
                if value or isinstance(value, (bool, int, long)):
                    d[prefix + attr] = value
        if hasattr(self, 'display') and self.display:
            d['display'] = self.display
        return d


class Gender(Field):
    children = ('content', )

    genders = set(['male', 'female'])

    def __init__(self, content=None, valid_since=None, inferred=None):
        """
        `content` is the gender value. One of Gender.genders.

        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.
        """
        super(Gender, self).__init__(valid_since, inferred)
        self._content = None
        self.content = content

    @property
    def display(self):
        if self.content:
            return self.content.title()

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        if value.lower() not in self.genders:
            raise ValueError("Gender unknown")
        self._content = value


class Ethnicity(Field):
    """
    An ethnicity value.
    The content will be a string with one of the following values (based on US census definitions):

    """
    children = ('content', )

    def __init__(self, content=None, valid_since=None, inferred=None):
        """
        `content` is the ethnicity value. One of: 'white', 'black', 'american_indian', 'alaska_nativeian_indian',
            'chinese', 'filipino', 'other_asian', 'japanese',
            'korean', 'viatnamese', 'native_hawaiian', 'guamanian',
            'chamorro', 'samoan', 'other_pacific_islander', 'other'.

        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.
        """
        super(Ethnicity, self).__init__(valid_since, inferred)
        self.content = content.lower()

    @property
    def display(self):
        if self.content:
            return self.content.replace("_", " ").title()


class Name(Field):
    """A name of a person."""

    attributes = ('type',)
    children = ('prefix', 'first', 'middle', 'last', 'suffix', 'raw', 'display')
    types_set = set(['present', 'maiden', 'former', 'alias'])

    def __init__(self, prefix=None, first=None, middle=None, last=None,
                 suffix=None, raw=None, display=None, type_=None, valid_since=None, inferred=None):
        """`prefix`, `first`, `middle`, `last`, `suffix`, `raw`, `type_`, 
        should all be unicode objects or utf8 encoded strs (will be decoded 
        automatically).
        
        `raw` is an unparsed name like "Clark J. Kent", usefull when you
        want to search by name and don't want to work hard to parse it.
        Note that in response data there's never name.raw, the names in 
        the response are always parsed, this is only for querying with 
        an unparsed name.
        
        `type_` is one of Name.types_set.
        
        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.
        
        """
        Field.__init__(self, valid_since, inferred)
        self.prefix = prefix
        self.first = first
        self.middle = middle
        self.last = last
        self.suffix = suffix
        self.raw = raw
        self.type = type_
        self._display = display

    @property
    def is_searchable(self):
        """A bool value that indicates whether the name is a valid name to 
        search by."""
        first = alpha_chars(self.first or u'')
        last = alpha_chars(self.last or u'')
        raw = alpha_chars(self.raw or u'')
        return (len(first) >= 2 and len(last) >= 2) or len(raw) >= 4


class Address(Field):
    """An address of a person."""

    attributes = ('type',)
    children = ('country', 'state', 'city', 'po_box', 'zip_code',
                'street', 'house', 'apartment', 'raw', 'display')
    types_set = set(['home', 'work', 'old'])

    def __init__(self, country=None, state=None, city=None, po_box=None,
                 street=None, house=None, zip_code=None, apartment=None, raw=None,
                 display=None, type_=None, valid_since=None, inferred=None):
        """`country`, `state`, `city`, `po_box`, `street`, `house`, `apartment`, 
        `raw`, `zip_code`, `display` and `type_` should all be unicode objects or utf8 encoded strs
        (will be decoded automatically).
        
        `country` and `state` are country code (like "US") and state code 
        (like "NY"), note that the full value is available as 
        address.country_full and address.state_full.
        
        `raw` is an unparsed address like "123 Marina Blvd, San Francisco, 
        California, US", usefull when you want to search by address and don't 
        want to work hard to parse it.
        Note that in response data there's never address.raw, the addresses in 
        the response are always parsed, this is only for querying with 
        an unparsed address.
        
        `type_` is one of Address.types_set.
        
        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.
        
        """
        Field.__init__(self, valid_since, inferred)
        self.country = country
        self.state = state
        self.city = city
        self.zip_code = zip_code
        self.po_box = po_box
        self.street = street
        self.house = house
        self.apartment = apartment
        self.raw = raw
        self.type = type_
        self._display = display

    @property
    def is_searchable(self):
        """A bool value that indicates whether the address is a valid address
        to search by."""
        return self.raw or (self.is_valid_country and (self.zip_code or self.is_valid_state or not self.state))

    @property
    def is_valid_country(self):
        """A bool value that indicates whether the object's country is a valid
        country code."""
        return self.country is not None and self.country.upper() in COUNTRIES

    @property
    def is_valid_state(self):
        """A bool value that indicates whether the object's state is a valid 
        state code."""
        return self.is_valid_country and self.country.upper() in STATES and \
               self.state is not None and \
               self.state.upper() in STATES[self.country.upper()]

    @property
    def country_full(self):
        """unicode, the full name of the object's country.
        
        >>> address = Address(country='FR')
        >>> address.country
        u'FR'
        >>> address.country_full
        u'France'
        
        """
        if self.country:
            return COUNTRIES.get(self.country.upper())

    @property
    def state_full(self):
        """unicode, the full name of the object's state.
        
        >>> address = Address(country='US', state='CO')
        >>> address.state
        u'CO'
        >>> address.state_full
        u'Colorado'
        
        """

        if self.is_valid_state:
            return STATES[self.country.upper()].get(self.state.upper())


class Phone(Field):
    """A phone number of a person."""

    attributes = ('type',)
    children = ('country_code', 'number', 'extension', 'raw', 'display', 'display_international')
    types_set = set(['mobile', 'home_phone', 'home_fax', 'work_phone',
                     'work_fax', 'pager'])

    def __init__(self, country_code=None, number=None, raw=None, extension=None, display=None,
                 display_international=None, type_=None, valid_since=None, inferred=None):
        """`country_code`, `number` and `extension` should all be int/long.
        
        `type_` is one of Phone.types_set.
        `raw` is a raw phone number string
        
        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.
        
        """
        Field.__init__(self, valid_since, inferred)
        self.country_code = country_code
        self.number = number
        self.raw = raw
        self.extension = extension
        self.type = type_
        self._display = display
        self.display_international = display_international

    @property
    def is_searchable(self):
        """A bool value that indicates whether the phone is a valid phone 
        to search by."""
        return (self.number and self.country_code) or self.raw

    def to_dict(self):
        """Extend Field.to_dict, take the display_international attribute."""
        d = Field.to_dict(self)
        if self.display_international:
            d['display_international'] = self.display_international
        return d


class Email(Field):
    """An email address of a person with the md5 of the address, might come
    in some cases without the address itself and just the md5 (for privacy 
    reasons).
    
    """

    attributes = ('type', 'disposable', 'email_provider')
    children = ('address', 'address_md5')
    types_set = set(['personal', 'work'])
    re_email = re.compile('^[\w.%\-+]+@[\w.%\-]+\.[a-zA-Z]{2,6}$')

    def __init__(self, address=None, address_md5=None, type_=None,
                 disposable=None, email_provider=None, valid_since=None, inferred=None):
        """`address`, `address_md5`, `type_` should be unicode objects or utf8 
        encoded strs (will be decoded automatically).
        
        `disposable` is a bool, indicating whether this is an 
        address from a disposable email service.

        `email_provider` is a boolean indicating whether this email 
        is provided by a public email provider (such as gmail, outlook.com, etc).

        `type_` is one of Email.types_set.
        
        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.
        
        """
        Field.__init__(self, valid_since, inferred)
        self.address = address
        self.address_md5 = address_md5
        self.type = type_
        self.email_provider = email_provider
        self.disposable = disposable

    @property
    def is_valid_email(self):
        """A bool value that indicates whether the address is a valid 
        email address.
        
        Note that the check is done be matching to the regular expression 
        at Email.re_email which is very basic and far from covering end-cases...
        
        """
        return bool(self.address and Email.re_email.match(self.address))

    @property
    def is_searchable(self):
        """A bool value that indicates whether the it's possible to search using the
        data in this email field (email address or md5)."""
        return self.is_valid_email or (self.address_md5 and len(self.address_md5) == 32)

    @property
    def username(self):
        """unicode, the username part of the email or None if the email is 
        invalid.
        
        >>> email = Email(address='clark.kent@example.com')
        >>> email.username
        u'clark'
        
        """
        if not self.is_valid_email:
            return
        return self.address.split('@')[0]

    @property
    def domain(self):
        """unicode, the domain part of the email or None if the email is 
        invalid.
        
        >>> email = Email(address='clark.kent@example.com')
        >>> email.domain
        u'example.com'
        
        """
        if not self.is_valid_email:
            return
        return self.address.split('@')[1]

    @property
    def display(self):
        return self.address or self.address_md5


class Job(Field):
    """Job information of a person."""

    children = ('title', 'organization', 'industry', 'date_range', 'display')

    def __init__(self, title=None, organization=None, industry=None, display=None,
                 date_range=None, valid_since=None, inferred=None):
        """`title`, `organization`, `industry`, should all be unicode objects 
        or utf8 encoded strs (will be decoded automatically).
        
        `date_range` is A DateRange object (piplapis.data.fields.DateRange), 
        that's the time the person held this job.
        
        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.
        
        """
        Field.__init__(self, valid_since, inferred)
        self.title = title
        self.organization = organization
        self.industry = industry
        self.date_range = date_range
        self._display = display


class Education(Field):
    """Education information of a person."""

    children = ('degree', 'school', 'date_range', 'display')

    def __init__(self, degree=None, school=None, date_range=None, display=None,
                 valid_since=None, inferred=None):
        """`degree` and `school` should both be unicode objects or utf8 encoded 
        strs (will be decoded automatically).
        
        `date_range` is A DateRange object (piplapis.data.fields.DateRange), 
        that's the time the person was studying.
        
        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.
        
        """
        Field.__init__(self, valid_since, inferred)
        self.degree = degree
        self.school = school
        self.date_range = date_range
        self._display = display


class Image(Field):
    """A URL of an image of a person."""

    children = ('url', 'thumbnail_token')

    def __init__(self, url=None, thumbnail_token=None, valid_since=None, inferred=None):
        """`url` should be a unicode object or utf8 encoded str (will be decoded 
        automatically).
        
        `thumbnail_token` is used to create the URL for Pipl's thumbnail service.

        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.
        
        """
        Field.__init__(self, valid_since, inferred)
        self.url = url
        self.thumbnail_token = thumbnail_token

    @property
    def is_valid_url(self):
        """A bool value that indicates whether the image URL is a valid URL."""
        return bool(self.url and is_valid_url(self.url))

    def get_thumbnail_url(self, width=100, height=100, zoom_face=True, favicon=True, use_https=False):
        if self.thumbnail_token:
            params = {
                "height": height,
                "width": width,
                "favicon": favicon,
                "zoom_face": zoom_face,
            }
            thumb_url_base = "{}://thumb.pipl.com/image?token={}&".format("https" if use_https else "http",
                                                                          self.thumbnail_token)
            return thumb_url_base + urlencode(params)

    @property
    def display(self):
        return self.url


class OriginCountry(Field):
    """An origin country of the person.
    """

    children = ('country', )

    def __init__(self, country=None, valid_since=None, inferred=None):
        """`country` is the country itself, it should be a unicode object or 
        a utf8 encoded str (will be decoded automatically). Possible values are 
        two-letter country codes.
        
        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.
        
        """
        Field.__init__(self, valid_since, inferred)
        self.country = country

    @property
    def display(self):
        if self.country:
            return COUNTRIES.get(self.country.upper())


class Language(Field):
    """A language the person is familiar with."""

    children = ('language', 'region', 'display')

    def __init__(self, language=None, region=None, display=None, valid_since=None, inferred=None):
        """`language` and `region` should be unicode objects 
        or utf8 encoded strs (will be decoded automatically).
        
        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.
        
        """
        Field.__init__(self, valid_since, inferred)
        self.language = language
        self.region = region
        self._display = display


class Username(Field):
    """A username/screen-name associated with the person.
    
    Note that even though in many sites the username uniquely identifies one 
    person it's not guarenteed, some sites allow different people to use the 
    same username.
    
    """

    def __init__(self, content=None, valid_since=None, inferred=None):
        """`content` is the username itself, it should be a unicode object or 
        a utf8 encoded str (will be decoded automatically).
        
        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.
        
        """
        Field.__init__(self, valid_since, inferred)
        self.content = content

    @property
    def display(self):
        return self.content

    @property
    def is_searchable(self):
        """A bool value that indicates whether the username is a valid username 
        to search by."""
        return len(alnum_chars(self.content or u'')) >= 4


class UserID(Field):
    """An ID associated with a person.
    
    The ID is a string that's used by the site to uniquely identify a person, 
    it's guaranteed that in the site this string identifies exactly one person.
    
    """

    def __init__(self, content=None, valid_since=None, inferred=None):
        """`content` is the ID itself, it should be a unicode object or a utf8 
        encoded str (will be decoded automatically).
        
        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.
        
        """
        Field.__init__(self, valid_since, inferred)
        self.content = content

    @property
    def display(self):
        return self.content


class DOB(Field):
    """Date-of-birth of A person.
    Comes as a date-range (the exact date is within the range, if the exact 
    date is known the range will simply be with start=end).
    
    """

    children = ('date_range', 'display')

    def __init__(self, date_range=None, display=None, valid_since=None, inferred=None):
        """`date_range` is A DateRange object (piplapis.data.fields.DateRange), 
        the date-of-birth is within this range.
        
        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.
        
        """
        Field.__init__(self, valid_since, inferred)
        self.date_range = date_range
        self._display = display

    @property
    def is_searchable(self):
        return self.date_range is not None

    @property
    def age(self):
        """int, the estimated age of the person.
        
        Note that A DOB object is based on a date-range and the exact date is 
        usually unknown so for age calculation the the middle of the range is 
        assumed to be the real date-of-birth. 
        
        """
        if self.date_range is None:
            return
        dob = self.date_range.middle
        today = datetime.date.today()
        if (today.month, today.day) < (dob.month, dob.day):
            return today.year - dob.year - 1
        else:
            return today.year - dob.year

    @property
    def age_range(self):
        """A tuple of two ints - the minimum and maximum age of the person."""
        if self.date_range is None:
            return None, None
        start_date = DateRange(self.date_range.start, self.date_range.start)
        end_date = DateRange(self.date_range.end, self.date_range.end)
        start_age = DOB(date_range=end_date).age
        end_age = DOB(date_range=start_date).age
        return start_age, end_age

    @staticmethod
    def from_birth_year(birth_year):
        """Take a person's birth year (int) and return a new DOB object 
        suitable for him."""
        if birth_year <= 0:
            raise ValueError('birth_year must be positive')
        date_range = DateRange.from_years_range(birth_year, birth_year)
        return DOB(date_range=date_range)

    @staticmethod
    def from_birth_date(birth_date):
        """Take a person's birth date (datetime.date) and return a new DOB 
        object suitable for him."""
        if birth_date > datetime.date.today():
            raise ValueError('birth_date can\'t be in the future')
        date_range = DateRange(birth_date, birth_date)
        return DOB(date_range=date_range)

    @staticmethod
    def from_age(age):
        """Take a person's age (int) and return a new DOB object 
        suitable for him."""
        return DOB.from_age_range(age, age)

    @staticmethod
    def from_age_range(start_age, end_age):
        """Take a person's minimal and maximal age and return a new DOB object 
        suitable for him."""
        if start_age < 0 or end_age < 0:
            raise ValueError('start_age and end_age can\'t be negative')

        if start_age > end_age:
            start_age, end_age = end_age, start_age

        today = datetime.date.today()

        try:
            start_date = today.replace(year=today.year - end_age - 1)
        except ValueError:  # February 29
            start_date = today.replace(year=today.year - end_age - 1, day=28)
        start_date += datetime.timedelta(days=1)

        try:
            end_date = today.replace(year=today.year - start_age)
        except ValueError:  # February 29
            end_date = today.replace(year=today.year - start_age, day=28)

        date_range = DateRange(start_date, end_date)
        return DOB(date_range=date_range)


class URL(Field):
    """A URL that's related to a person. Can either be a source of data
    about the person, or a URL otherwise related to the person.
    """

    attributes = ('category', 'sponsored', 'domain', 'name', 'source_id')
    children = ('url', )
    categories_set = set(['background_reports', 'contact_details', 'email_address',
                          'media', 'personal_profiles', 'professional_and_business',
                          'public_records', 'publications', 'school_and_classmates', 'web_pages'])

    def __init__(self, url=None, category=None, sponsored=None,
                 domain=None, name=None, source_id=None, valid_since=None, inferred=None):
        """
        `url` is the URL address itself
        `domain` is the URL's domain
        `name` is the website name
        `category` is one of URL.categories_set

        `url`, `category`, `domain` and `name` should all be unicode 
        objects or utf8 encoded strs (will be decoded automatically).
        
        `sponsored` is a boolean - whether the URL is sponsored or not
        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.
        
        """
        Field.__init__(self, valid_since, inferred)
        self.url = url
        self.domain = domain
        self.sponsored = sponsored
        self.name = name
        self.category = category
        self.source_id = source_id

    @property
    def is_valid_url(self):
        """A bool value that indicates whether the URL is a valid URL."""
        return bool(self.url and is_valid_url(self.url))

    @property
    def display(self):
        return self.url or self.name


class Tag(Field):
    """A general purpose element that holds any meaningful string that's
    related to the person.
    Used for holding data about the person that either couldn't be clearly
    classified or was classified as something different than the available
    data fields.

    """

    attributes = ('classification',)

    def __init__(self, content=None, classification=None, valid_since=None, inferred=None):
        """`content` is the tag itself, both `content` and `classification`
        should be unicode objects or utf8 encoded strs (will be decoded
        automatically).

        `valid_since` is a datetime.datetime object, it's the first time Pipl's
        crawlers found this data on the page.

        """
        Field.__init__(self, valid_since, inferred)
        self.content = content
        self.classification = classification

    @property
    def display(self):
        return self.content


class DateRange(Serializable):
    """A time intervel represented as a range of two dates.
    
    DateRange objects are used inside DOB, Job and Education objects.
    
    """

    def __init__(self, start, end):
        """`start` and `end` are datetime.date objects, both are required.
        
        For creating a DateRange object for an exact date (like if exact 
        date-of-birth is known) just pass the same value for `start` and `end`.
        
        """
        if start > end:
            start, end = end, start
        self.start = start
        self.end = end

    def __unicode__(self):
        """Return the unicode representation of the object."""
        return u' - '.join([unicode(self.start), unicode(self.end)])

    def __repr__(self):
        """Return a representation of the object (a valid value for eval())."""
        return 'DateRange(%s, %s)' % (repr(self.start), repr(self.end))

    def __eq__(self, other):
        """Bool, indicates whether `self` and `other` have exactly the same 
        start date and end date."""
        return repr(self) == repr(other)

    @property
    def is_exact(self):
        """True if the object holds an exact date (start=end), 
        False otherwise."""
        return self.start == self.end

    @property
    def middle(self):
        """The middle of the date range (a datetime.date object)."""
        return self.start + (self.end - self.start) / 2

    @property
    def years_range(self):
        """A tuple of two ints - the year of the start date and the year of the 
        end date."""
        return self.start.year, self.end.year

    @staticmethod
    def from_years_range(start_year, end_year):
        """Transform a range of years (two ints) to a DateRange object."""
        start = datetime.date(start_year, 1, 1)
        end = datetime.date(end_year, 12, 31)
        return DateRange(start, end)

    @staticmethod
    def from_dict(d):
        """Transform the dict to a DateRange object."""
        start = d.get('start')
        end = d.get('end')
        if not (start and end):
            raise ValueError('DateRange must have both start and end')
        start = str_to_date(start)
        end = str_to_date(end)
        return DateRange(start, end)

    def to_dict(self):
        """Transform the date-range to a dict."""
        d = {}
        d['start'] = date_to_str(self.start)
        d['end'] = date_to_str(self.end)
        return d