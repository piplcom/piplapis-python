from piplapis.data.utils import Serializable


class AvailableData(Serializable):

    children = ('basic', 'premium')

    def __init__(self, basic=None, premium=None, *args, **kwargs):
        self.basic = basic
        self.premium = premium

    def to_dict(self):
        d = {}
        if self.basic is not None and type(self.basic) == FieldCount:
            d['basic'] = self.basic.to_dict()
        if self.premium is not None and type(self.premium) == FieldCount:
            d['premium'] = self.premium.to_dict()
        return d

    @classmethod
    def from_dict(cls, d):
        basic = d.get('basic')
        premium = d.get('premium')
        ins = cls()
        if basic is not None:
            ins.basic = FieldCount.from_dict(basic)
        if premium is not None:
            ins.premium = FieldCount.from_dict(premium)
        return ins


class FieldCount(Serializable):
    children = ('addresses', 'ethnicities', 'emails', 'dobs', 'genders', 'user_ids', 'social_profiles',
                'educations', 'jobs', 'images', 'languages', 'origin_countries', 'names', 'phones',
                'mobile_phones', 'landline_phones', 'relationships', 'usernames')

    def __init__(self, addresses=None, ethnicities=None, emails=None, dobs=None,
                 genders=None, user_ids=None, social_profiles=None, educations=None, jobs=None, images=None,
                 languages=None, origin_countries=None, names=None, phones=None, relationships=None,
                 usernames=None, mobile_phones=None, landline_phones=None, *args, **kwargs):
        """
        A summary of the data within an API response
        :param addresses: int, the number of addresses
        :param ethnicities: int, the number of ethnicities
        :param emails: int, the number of emails
        :param dobs: int, the number of dobs
        :param genders: int, the number of genders
        :param user_ids: int, the number of user ids
        :param social_profiles: int, the number of social profile sources
        :param educations: int, the number of educations
        :param jobs: int, the number of jobs
        :param images: int, the number of images
        :param languages: int, the number of languages
        :param origin_countries: int, the number of origin countries
        :param names: int, the number of names
        :param phones: int, the number of phones, both mobile and landline phones
        :param mobile_phones: int, the number of mobile phones
        :param landline_phones: int, the number of landline phones
        :param relationships: int, the number of relationships
        :param usernames: int, the number of usernames
        """

        self.dobs = dobs
        self.images = images
        self.educations = educations
        self.addresses = addresses
        self.jobs = jobs
        self.genders = genders
        self.ethnicities = ethnicities
        self.phones = phones
        self.mobile_phones = mobile_phones
        self.landline_phones = landline_phones
        self.origin_countries = origin_countries
        self.ethnicities = ethnicities
        self.usernames = usernames
        self.languages = languages
        self.emails = emails
        self.user_ids = user_ids
        self.relationships = relationships
        self.names = names
        self.social_profiles = social_profiles

    def to_dict(self):
        d = {}
        for child in self.children:
            if getattr(self, child):
                d[child] = getattr(self, child)
        return d

    @classmethod
    def from_dict(cls, d):
        kwargs = {}
        for key, value in d.items():
            if key in cls.children and type(value) == int:
                kwargs[key] = value
        return cls(**kwargs)
