# coding=utf-8
from __future__ import unicode_literals
import re
import json
import datetime

import six
from six import PY2

STATES = {
    'US': {'WA': 'Washington', 'VA': 'Virginia', 'DE': 'Delaware', 'DC': 'District Of Columbia', 'WI': 'Wisconsin', 'WV': 'West Virginia', 'HI': 'Hawaii', 'FL': 'Florida', 'YT': 'Yukon', 'WY': 'Wyoming', 'PR': 'Puerto Rico', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'TX': 'Texas', 'LA': 'Louisiana', 'NC': 'North Carolina', 'ND': 'North Dakota', 'NE': 'Nebraska', 'FM': 'Federated States Of Micronesia', 'TN': 'Tennessee', 'NY': 'New York', 'PA': 'Pennsylvania', 'CT': 'Connecticut', 'RI': 'Rhode Island', 'NV': 'Nevada', 'NH': 'New Hampshire', 'G': 'Guam', 'CO': 'Colorado', 'VI': 'Virgin Islands', 'AK': 'Alaska', 'AL': 'Alabama', 'AS': 'American Samoa', 'AR': 'Arkansas', 'VT': 'Vermont', 'IL': 'Illinois', 'GA': 'Georgia', 'IN': 'Indiana', 'IA': 'Iowa', 'MA': 'Massachusetts', 'AZ': 'Arizona', 'CA': 'California', 'ID': 'Idaho', 'PW': 'Pala', 'ME': 'Maine', 'MD': 'Maryland', 'OK': 'Oklahoma', 'OH': 'Ohio', 'UT': 'Utah', 'MO': 'Missouri', 'MN': 'Minnesota', 'MI': 'Michigan', 'MH': 'Marshall Islands', 'KS': 'Kansas', 'MT': 'Montana', 'MP': 'Northern Mariana Islands', 'MS': 'Mississippi', 'SC': 'South Carolina', 'KY': 'Kentucky', 'OR': 'Oregon', 'SD': 'South Dakota'},
    'CA': {'AB': 'Alberta', 'BC': 'British Columbia', 'MB': 'Manitoba', 'NB': 'New Brunswick', 'NT': 'Northwest Territories', 'NS': 'Nova Scotia', 'N': 'Nunavut', 'ON': 'Ontario', 'PE': 'Prince Edward Island', 'QC': 'Quebec', 'SK': 'Saskatchewan', 'Y': 'Yukon', 'NL': 'Newfoundland and Labrador'},
    'A': {'WA': 'State of Western Australia', 'SA': 'State of South Australia', 'NT': 'Northern Territory', 'VIC': 'State of Victoria', 'TAS': 'State of Tasmania', 'QLD': 'State of Queensland', 'NSW': 'State of New South Wales', 'ACT': 'Australian Capital Territory'},
    'GB': {'WLS': 'Wales', 'SCT': 'Scotland', 'NIR': 'Northern Ireland', 'ENG': 'England'},
}
COUNTRIES = {'BD': 'Bangladesh', 'WF': 'Wallis And Futuna Islands', 'BF': 'Burkina Faso', 'PY': 'Paraguay', 'BA': 'Bosnia And Herzegovina', 'BB': 'Barbados', 'BE': 'Belgium', 'BM': 'Bermuda', 'BN': 'Brunei Darussalam', 'BO': 'Bolivia', 'BH': 'Bahrain', 'BI': 'Burundi', 'BJ': 'Benin', 'BT': 'Bhutan', 'JM': 'Jamaica', 'BV': 'Bouvet Island', 'BW': 'Botswana', 'WS': 'Samoa', 'BR': 'Brazil', 'BS': 'Bahamas', 'JE': 'Jersey', 'BY': 'Belarus', 'BZ': 'Belize', 'R': 'Russian Federation', 'RW': 'Rwanda', 'LT': 'Lithuania', 'RE': 'Reunion', 'TM': 'Turkmenistan', 'TJ': 'Tajikistan', 'RO': 'Romania', 'LS': 'Lesotho', 'GW': 'Guinea-bissa', 'G': 'Guam', 'GT': 'Guatemala', 'GS': 'South Georgia And South Sandwich Islands', 'GR': 'Greece', 'GQ': 'Equatorial Guinea', 'GP': 'Guadeloupe', 'JP': 'Japan', 'GY': 'Guyana', 'GG': 'Guernsey', 'GF': 'French Guiana', 'GE': 'Georgia', 'GD': 'Grenada', 'GB': 'Great Britain', 'GA': 'Gabon', 'GN': 'Guinea', 'GM': 'Gambia', 'GL': 'Greenland', 'GI': 'Gibraltar', 'GH': 'Ghana', 'OM': 'Oman', 'TN': 'Tunisia', 'JO': 'Jordan', 'HR': 'Croatia', 'HT': 'Haiti', 'SV': 'El Salvador', 'HK': 'Hong Kong', 'HN': 'Honduras', 'HM': 'Heard And Mcdonald Islands', 'AD': 'Andorra', 'PR': 'Puerto Rico', 'PS': 'Palestine', 'PW': 'Pala', 'PT': 'Portugal', 'SJ': 'Svalbard And Jan Mayen Islands', 'VG': 'Virgin Islands, British', 'AI': 'Anguilla', 'KP': 'North Korea', 'PF': 'French Polynesia', 'PG': 'Papua New Guinea', 'PE': 'Per', 'PK': 'Pakistan', 'PH': 'Philippines', 'PN': 'Pitcairn', 'PL': 'Poland', 'PM': 'Saint Pierre And Miquelon', 'ZM': 'Zambia', 'EH': 'Western Sahara', 'EE': 'Estonia', 'EG': 'Egypt', 'ZA': 'South Africa', 'EC': 'Ecuador', 'IT': 'Italy', 'AO': 'Angola', 'KZ': 'Kazakhstan', 'ET': 'Ethiopia', 'ZW': 'Zimbabwe', 'SA': 'Saudi Arabia', 'ES': 'Spain', 'ER': 'Eritrea', 'ME': 'Montenegro', 'MD': 'Moldova', 'MG': 'Madagascar', 'MA': 'Morocco', 'MC': 'Monaco', 'UZ': 'Uzbekistan', 'MM': 'Myanmar', 'ML': 'Mali', 'MO': 'Maca', 'MN': 'Mongolia', 'MH': 'Marshall Islands', 'US': 'United States', 'UM': 'United States Minor Outlying Islands', 'MT': 'Malta', 'MW': 'Malawi', 'MV': 'Maldives', 'MQ': 'Martinique', 'MP': 'Northern Mariana Islands', 'MS': 'Montserrat', 'NA': 'Namibia', 'IM': 'Isle Of Man', 'UG': 'Uganda', 'MY': 'Malaysia', 'MX': 'Mexico', 'IL': 'Israel', 'BG': 'Bulgaria', 'FR': 'France', 'AW': 'Aruba', 'AX': '\xc3\x85land', 'FI': 'Finland', 'FJ': 'Fiji', 'FK': 'Falkland Islands', 'FM': 'Micronesia', 'FO': 'Faroe Islands', 'NI': 'Nicaragua', 'NL': 'Netherlands', 'NO': 'Norway', 'SO': 'Somalia', 'NC': 'New Caledonia', 'NE': 'Niger', 'NF': 'Norfolk Island', 'NG': 'Nigeria', 'NZ': 'New Zealand', 'NP': 'Nepal', 'NR': 'Naur', 'N': 'Niue', 'MR': 'Mauritania', 'CK': 'Cook Islands', 'CI': "C\xc3\xb4te D'ivoire", 'CH': 'Switzerland', 'CO': 'Colombia', 'CN': 'China', 'CM': 'Cameroon', 'CL': 'Chile', 'CC': 'Cocos (keeling) Islands', 'CA': 'Canada', 'CG': 'Congo (brazzaville)', 'CF': 'Central African Republic', 'CD': 'Congo (kinshasa)', 'CZ': 'Czech Republic', 'CY': 'Cyprus', 'CX': 'Christmas Island', 'CS': 'Serbia', 'CR': 'Costa Rica', 'H': 'Hungary', 'CV': 'Cape Verde', 'C': 'Cuba', 'SZ': 'Swaziland', 'SY': 'Syria', 'KG': 'Kyrgyzstan', 'KE': 'Kenya', 'SR': 'Suriname', 'KI': 'Kiribati', 'KH': 'Cambodia', 'KN': 'Saint Kitts And Nevis', 'KM': 'Comoros', 'ST': 'Sao Tome And Principe', 'SK': 'Slovakia', 'KR': 'South Korea', 'SI': 'Slovenia', 'SH': 'Saint Helena', 'KW': 'Kuwait', 'SN': 'Senegal', 'SM': 'San Marino', 'SL': 'Sierra Leone', 'SC': 'Seychelles', 'SB': 'Solomon Islands', 'KY': 'Cayman Islands', 'SG': 'Singapore', 'SE': 'Sweden', 'SD': 'Sudan', 'DO': 'Dominican Republic', 'DM': 'Dominica', 'DJ': 'Djibouti', 'DK': 'Denmark', 'DE': 'Germany', 'YE': 'Yemen', 'AT': 'Austria', 'DZ': 'Algeria', 'MK': 'Macedonia', 'UY': 'Uruguay', 'YT': 'Mayotte', 'M': 'Mauritius', 'TZ': 'Tanzania', 'LC': 'Saint Lucia', 'LA': 'Laos', 'TV': 'Tuval', 'TW': 'Taiwan', 'TT': 'Trinidad And Tobago', 'TR': 'Turkey', 'LK': 'Sri Lanka', 'LI': 'Liechtenstein', 'LV': 'Latvia', 'TO': 'Tonga', 'TL': 'Timor-leste', 'L': 'Luxembourg', 'LR': 'Liberia', 'TK': 'Tokela', 'TH': 'Thailand', 'TF': 'French Southern Lands', 'TG': 'Togo', 'TD': 'Chad', 'TC': 'Turks And Caicos Islands', 'LY': 'Libya', 'VA': 'Vatican City', 'AC': 'Ascension Island', 'VC': 'Saint Vincent And The Grenadines', 'AE': 'United Arab Emirates', 'VE': 'Venezuela', 'AG': 'Antigua And Barbuda', 'AF': 'Afghanistan', 'IQ': 'Iraq', 'VI': 'Virgin Islands, U.s.', 'IS': 'Iceland', 'IR': 'Iran', 'AM': 'Armenia', 'AL': 'Albania', 'VN': 'Vietnam', 'AN': 'Netherlands Antilles', 'AQ': 'Antarctica', 'AS': 'American Samoa', 'AR': 'Argentina', 'A': 'Australia', 'V': 'Vanuat', 'IO': 'British Indian Ocean Territory', 'IN': 'India', 'LB': 'Lebanon', 'AZ': 'Azerbaijan', 'IE': 'Ireland', 'ID': 'Indonesia', 'PA': 'Panama', 'UA': 'Ukraine', 'QA': 'Qatar', 'MZ': 'Mozambique', 'BL': 'Saint Barthélemy', 'BQ': 'Caribbean Netherlands', 'MF': 'Saint Martin', 'SS': 'South Sudan', 'SX': 'Sint Maarten', 'XK': 'Kosovo', 'CW': 'Curaçao', 'RS': 'Serbia'}

TIMESTAMP_FORMAT = '%Y-%m-%d'
DATE_FORMAT = '%Y-%m-%d'

VALID_URL_REGEX = re.compile('^(?#Protocol)(?:(?:ht|f)tp(?:s?)\:\/\/|~\/|\/)?(?#Username:Password)(?:\w+:\w+@)?(?#Subdomains)(?:(?:[-\w]+\.)+(?#TopLevel Domains)(?:com|org|net|gov|mil|biz|info|mobi|name|aero|jobs|museum|travel|[a-z]{2}))(?#Port)(?::[\d]{1,5})?(?#Directories)(?:(?:(?:\/(?:[-\w~!$+|.,=]|%[a-f\d]{2})+)+|\/)+|\?|#)?(?#Query)(?:(?:\?(?:[-\w~!$+|.,*:]|%[a-f\d{2}])+=?(?:[-\w~!$+|.,*:=]|%[a-f\d]{2})*)(?:&(?:[-\w~!$+|.,*:]|%[a-f\d{2}])+=?(?:[-\w~!$+|.,*:=]|%[a-f\d]{2})*)*)*(?#Anchor)(?:#(?:[-\w~!$+|.,*:=]|%[a-f\d]{2})*)?$')


class Serializable(object):
    
    """The base class of every class in the library that needs the ability to
    be serialized/deserialized to/from a JSON string.
    
    Every inherited class must implement its own to_dict method that transforms
    an object to a dict and from_dict method that transforms a dict to 
    an object.
    """
    
    @classmethod
    def from_json(cls, json_str):
        """
        Deserialize the object from a JSON string.
        :param json_str: str or unicode. The JSON string to deserialize.
        """
        d = json.loads(json_str)
        return cls.from_dict(d)
        
    def to_json(self):
        """Serialize the object to a JSON string."""
        d = self.to_dict()
        return json.dumps(d)

    def to_dict(self):
        raise NotImplementedError

    @classmethod
    def from_dict(cls, d):
        raise NotImplementedError


def str_to_datetime(s):
    """Transform an str object to a datetime object.
    :param s: str or unicode. The datetime string.
    """
    return datetime.datetime.strptime(s, TIMESTAMP_FORMAT)


def datetime_to_str(dt):
    """Transform a datetime object to an str object.
    :param dt: datetime object to convert to a string.
    """
    return dt.strftime(TIMESTAMP_FORMAT)


def str_to_date(s):
    """Transform an str object to a date object.
    :param s: str or unicode. The date string.
    """
    return datetime.datetime.strptime(s, DATE_FORMAT).date()


def date_to_str(d):
    """Transform a date object to an str object.
    :param d: date object to convert to a string.
    """
    return d.isoformat()


def is_valid_url(url):
    """Return True if `url` (str/unicode) is a valid URL, False otherwise.
    :param url: str or unicode. The URL to validate.
    """
    return bool(VALID_URL_REGEX.search(url))


def alpha_chars(s):
    """Strip all non alphabetic characters from the str/unicode `s`.
    :param s: str or unicode. The string to strip.
    """
    return ''.join([c for c in s if c.isalpha()])
    
    
def alnum_chars(s):
    """Strip all non alphanumeric characters from the str/unicode `s`.
    :param s: str or unicode. The string to strip.
    """
    return ''.join([c for c in s if c.isalnum()])


def to_utf8(obj):
    """Return str representation of obj, if s is a unicode object it's encoded
    with utf8.
    :param obj: The object to represent in utf8.
    """

    if isinstance(obj, six.text_type):
        return obj.encode('utf8')
    elif PY2:
        return str(obj)
    else:
        bytes(obj)


def to_unicode(obj):
    """Return unicode representation of obj, if s is an str object it's decoded
    with utf8.
    :param obj: The object to decode to unicode.

    """
    if isinstance(obj, six.binary_type):
        return obj.decode('utf8')
    elif PY2:
        return six.u(obj)
    else:
        return str(obj)
