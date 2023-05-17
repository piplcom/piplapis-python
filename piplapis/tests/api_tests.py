import logging
import os
from unittest import TestCase

from piplapis.data import (
    DOB,
    URL,
    Address,
    Email,
    Gender,
    Image,
    Language,
    Name,
    OriginCountry,
    Person,
    Phone,
    UserID,
    Username,
)
from piplapis.data.containers import Relationship
from piplapis.search import SearchAPIRequest, SearchAPIResponse

# Tests for the pipl API using the python client library
# These tests expect two environment variables to be set:
# TESTING_KEY: the API key to use
# API_TESTS_BASE_URL: the base URL on which to execute requests

handler = logging.StreamHandler()
logging.getLogger("piplapis").addHandler(handler)
logger = logging.getLogger("piplapis")
logger.warning("The api_tests module API in piplapis.tests is deprecated & does not receive updates.")


class APITests(TestCase):
    def setUp(self) -> None:
        SearchAPIRequest.default_api_key = os.getenv("TESTING_KEY")
        SearchAPIRequest.BASE_URL = os.getenv("API_TESTS_BASE_URL") + "?developer_class=business_premium"

    def get_broad_search_request(self) -> SearchAPIRequest:
        return SearchAPIRequest(first_name="brian", last_name="perks")

    def get_narrow_search_request(self) -> SearchAPIRequest:
        return SearchAPIRequest(email="garth.moulton@pipl.com")

    def get_narrow_md5_search_request(self) -> SearchAPIRequest:
        return SearchAPIRequest(person=Person(fields=[Email(address_md5="b095275aa233df8e857dbca662512ca4")]))

    def test_basic_request(self) -> None:
        response = self.get_broad_search_request().send()
        self.assertEqual(response.http_status_code, 200)

    def test_search_makes_a_match_request(self) -> None:
        response = self.get_narrow_search_request().send()
        self.assertEqual(response.http_status_code, 200)
        self.assertIsNotNone(response.person)

    def test_recursive_request(self) -> None:
        response = self.get_broad_search_request().send()
        self.assertGreater(len(response.possible_persons), 0)
        second_response = SearchAPIRequest(search_pointer=response.possible_persons[0].search_pointer).send()
        self.assertIsNotNone(second_response.person)

    def test_make_sure_hide_sponsored_works(self) -> None:
        request = self.get_narrow_search_request()
        request.hide_sponsored = True
        response = request.send()
        sponsored_links = [x for x in response.person.urls if x.sponsored]
        self.assertEqual(len(sponsored_links), 0)

    def test_make_sure_we_can_hide_inferred(self) -> None:
        request = self.get_narrow_search_request()
        request.minimum_probability = 1.0
        response = request.send()
        inferred_data = [x for x in response.person.all_fields if x.inferred]
        self.assertEqual(len(inferred_data), 0)

    def test_make_sure_we_get_inferred(self) -> None:
        request = self.get_narrow_search_request()
        request.minimum_probability = 0.5
        response = request.send()
        inferred_data = [x for x in response.person.all_fields if x.inferred]
        self.assertGreater(len(inferred_data), 0)

    def test_make_sure_show_sources_matching_works(self) -> None:
        request = self.get_narrow_search_request()
        request.show_sources = "matching"
        response = request.send()
        self.assertGreater(len(response.sources), 0)
        non_matching_sources = [x for x in response.sources if x.person_id != response.person.person_id]
        self.assertEqual(len(non_matching_sources), 0)

    def test_make_sure_show_sources_all_works(self) -> None:
        request = self.get_narrow_search_request()
        request.show_sources = "all"
        response = request.send()
        non_matching_sources = [x for x in response.sources if x.person_id != response.person.person_id]
        self.assertGreater(len(non_matching_sources), 0)

    def test_make_sure_minimum_match_works(self) -> None:
        request = self.get_broad_search_request()
        request.minimum_match = 0.7
        response = request.send()
        persons_below_match = [x for x in response.possible_persons if x.match < 0.7]
        self.assertEqual(len(persons_below_match), 0)

    def test_make_sure_deserialization_works(self) -> None:
        response = SearchAPIRequest(email="clark.kent@example.com").send()
        self.assertEqual(response.person.names[0].display, "Kal El")
        self.assertEqual(response.person.emails[1].address_md5, "999e509752141a0ee42ff455529c10fc")
        self.assertEqual(response.person.usernames[0].content, "superman@facebook")
        self.assertEqual(response.person.addresses[1].display, "10-1 Hickory Lane, Smallville, Kansas")
        self.assertEqual(response.person.jobs[0].display, "Field Reporter at The Daily Planet (2000-2012)")
        self.assertEqual(response.person.educations[0].degree, "B.Sc Advanced Science")

    def test_make_sure_md5_search_works(self) -> None:
        self.assertIsNotNone(self.get_narrow_md5_search_request().send().person)

    def test_contact_datatypes_are_as_expected(self) -> None:
        SearchAPIRequest.BASE_URL = os.getenv("API_TESTS_BASE_URL") + "?developer_class=contact"
        response = self.get_narrow_search_request().send()
        available_data_types = {Name, Gender, DOB, URL, Language, OriginCountry, Address, Phone}
        for field in response.person.all_fields:
            if type(field) == Email:
                self.assertEqual(field.address, "full.email.available@business.subscription")
            else:
                self.assertIn(type(field), available_data_types)

    def test_social_datatypes_are_as_expected(self) -> None:
        SearchAPIRequest.BASE_URL = os.getenv("API_TESTS_BASE_URL") + "?developer_class=social"
        response = self.get_narrow_search_request().send()
        available_data_types = {
            Name,
            Gender,
            DOB,
            Language,
            OriginCountry,
            Address,
            Phone,
            Username,
            UserID,
            Image,
            Relationship,
            URL,
        }
        for field in response.person.all_fields:
            if type(field) == Email:
                self.assertEqual(field.address, "full.email.available@business.subscription")
            else:
                self.assertIn(type(field), available_data_types)

    def test_forward_compatibility(self) -> None:
        SearchAPIRequest.BASE_URL += "&show_unknown_fields=1"
        request = SearchAPIRequest(email="clark.kent@example.com")
        response = request.send()
        self.assertIsNotNone(response.person)

    def test_make_sure_insufficient_search_isnt_sent(self) -> None:
        with self.assertRaises(Exception):
            SearchAPIRequest(first_name="brian").send()

    def test_make_sure_field_count_is_correct_on_premium(self) -> None:
        res = self.get_narrow_search_request().send()
        self.assertEqual(res.available_data.premium.relationships, 22)
        self.assertEqual(res.available_data.premium.usernames, 4)
        self.assertEqual(res.available_data.premium.jobs, 18)
        self.assertEqual(res.available_data.premium.addresses, 17)
        self.assertEqual(res.available_data.premium.phones, 11)
        self.assertEqual(res.available_data.premium.emails, 7)
        self.assertEqual(res.available_data.premium.languages, 1)
        self.assertEqual(res.available_data.premium.names, 2)
        self.assertEqual(res.available_data.premium.dobs, 1)
        self.assertEqual(res.available_data.premium.images, 4)
        self.assertEqual(res.available_data.premium.genders, 1)
        self.assertEqual(res.available_data.premium.educations, 2)
        self.assertEqual(res.available_data.premium.social_profiles, 7)

    def test_make_sure_field_count_is_correct_on_basic(self) -> None:
        SearchAPIRequest.BASE_URL = os.getenv("API_TESTS_BASE_URL") + "?developer_class=social"
        res = self.get_narrow_search_request().send()
        self.assertEqual(res.available_data.basic.relationships, 12)
        self.assertEqual(res.available_data.basic.usernames, 3)
        self.assertEqual(res.available_data.basic.addresses, 2)
        self.assertEqual(res.available_data.basic.emails, 4)
        self.assertEqual(res.available_data.basic.user_ids, 6)
        self.assertEqual(res.available_data.basic.languages, 1)
        self.assertEqual(res.available_data.basic.names, 1)
        self.assertEqual(res.available_data.basic.images, 2)
        self.assertEqual(res.available_data.basic.genders, 1)
        self.assertEqual(res.available_data.basic.social_profiles, 6)

    def test_response_class_default(self) -> None:
        request = SearchAPIRequest(email="clark.kent@example.com")
        response = request.send()
        self.assertIsInstance(response, SearchAPIResponse)

    def test_response_class_custom(self) -> None:
        custom_response_class = type("CustomResponseClass", (SearchAPIResponse,), {})
        request = SearchAPIRequest(email="clark.kent@example.com", response_class=custom_response_class)
        response = request.send()
        self.assertIsInstance(response, custom_response_class)
