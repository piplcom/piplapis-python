import logging
import os
from piplapis.data import (
    Person,
    Email,
    Name,
    URL,
    Username,
    UserID,
    Image,
    Phone,
    Address,
    OriginCountry,
    Language,
    DOB,
    Gender,
)
from piplapis.data.containers import Relationship
from piplapis.search import SearchAPIRequest, SearchAPIResponse
from unittest import TestCase


# Tests for the pipl API using the python client library
# These tests expect two environment variables to be set:
# TESTING_KEY: the API key to use
# API_TESTS_BASE_URL: the base URL on which to execute requests

handler = logging.StreamHandler()
logging.getLogger("piplapis").addHandler(handler)
logger = logging.getLogger("piplapis")
logger.warning(
    "The api_tests module API in piplapis.tests is deprecated & does not receive updates."
)


class APITests(TestCase):
    def setUp(self):
        SearchAPIRequest.default_api_key = os.getenv("TESTING_KEY")
        SearchAPIRequest.BASE_URL = (
            os.getenv("API_TESTS_BASE_URL") + "?developer_class=business_premium"
        )

    def get_broad_search_request(self):
        return SearchAPIRequest(first_name="brian", last_name="perks")

    def get_narrow_search_request(self):
        return SearchAPIRequest(email="brianperks@gmail.com")

    def get_narrow_md5_search_request(self):
        return SearchAPIRequest(
            person=Person(
                fields=[Email(address_md5="e34996fda036d60aa2a595ca86ed8fef")]
            )
        )

    def test_basic_request(self):
        response = self.get_broad_search_request().send()
        self.assertEquals(response.http_status_code, 200)

    def test_search_makes_a_match_request(self):
        response = self.get_narrow_search_request().send()
        self.assertEquals(response.http_status_code, 200)
        self.assertIsNotNone(response.person)

    def test_recursive_request(self):
        response = self.get_broad_search_request().send()
        self.assertGreater(len(response.possible_persons), 0)
        second_response = SearchAPIRequest(
            search_pointer=response.possible_persons[0].search_pointer
        ).send()
        self.assertIsNotNone(second_response.person)

    def test_make_sure_hide_sponsored_works(self):
        request = self.get_narrow_search_request()
        request.hide_sponsored = True
        response = request.send()
        sponsored_links = [x for x in response.person.urls if x.sponsored]
        self.assertEquals(len(sponsored_links), 0)

    def test_make_sure_we_can_hide_inferred(self):
        request = self.get_narrow_search_request()
        request.minimum_probability = 1.0
        response = request.send()
        inferred_data = [x for x in response.person.all_fields if x.inferred]
        self.assertEquals(len(inferred_data), 0)

    def test_make_sure_we_get_inferred(self):
        request = self.get_narrow_search_request()
        request.minimum_probability = 0.5
        response = request.send()
        inferred_data = [x for x in response.person.all_fields if x.inferred]
        self.assertGreater(len(inferred_data), 0)

    def test_make_sure_show_sources_matching_works(self):
        request = self.get_narrow_search_request()
        request.show_sources = "matching"
        response = request.send()
        self.assertGreater(len(response.sources), 0)
        non_matching_sources = [
            x for x in response.sources if x.person_id != response.person.person_id
        ]
        self.assertEquals(len(non_matching_sources), 0)

    def test_make_sure_show_sources_all_works(self):
        request = self.get_narrow_search_request()
        request.show_sources = "all"
        response = request.send()
        non_matching_sources = [
            x for x in response.sources if x.person_id != response.person.person_id
        ]
        self.assertGreater(len(non_matching_sources), 0)

    def test_make_sure_minimum_match_works(self):
        request = self.get_broad_search_request()
        request.minimum_match = 0.7
        response = request.send()
        persons_below_match = [x for x in response.possible_persons if x.match < 0.7]
        self.assertEquals(len(persons_below_match), 0)

    def test_make_sure_deserialization_works(self):
        response = SearchAPIRequest(email="clark.kent@example.com").send()
        self.assertEquals(response.person.names[0].display, "Clark Joseph Kent")
        self.assertEquals(
            response.person.emails[1].address_md5, "999e509752141a0ee42ff455529c10fc"
        )
        self.assertEquals(response.person.usernames[0].content, "superman@facebook")
        self.assertEquals(
            response.person.addresses[1].display,
            "1000-355 Broadway, Metropolis, Kansas",
        )
        self.assertEquals(
            response.person.jobs[0].display,
            "Field Reporter at The Daily Planet (2000-2012)",
        )
        self.assertEquals(response.person.educations[0].degree, "B.Sc Advanced Science")

    def test_make_sure_md5_search_works(self):
        self.assertIsNotNone(self.get_narrow_md5_search_request().send().person)

    def test_contact_datatypes_are_as_expected(self):
        SearchAPIRequest.BASE_URL = (
            os.getenv("API_TESTS_BASE_URL") + "?developer_class=contact"
        )
        response = self.get_narrow_search_request().send()
        available_data_types = {
            Name,
            Gender,
            DOB,
            URL,
            Language,
            OriginCountry,
            Address,
            Phone,
        }
        for field in response.person.all_fields:
            if type(field) == Email:
                self.assertEqual(
                    field.address, "full.email.available@business.subscription"
                )
            else:
                self.assertIn(type(field), available_data_types)

    def test_social_datatypes_are_as_expected(self):
        SearchAPIRequest.BASE_URL = (
            os.getenv("API_TESTS_BASE_URL") + "?developer_class=social"
        )
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
                self.assertEqual(
                    field.address, "full.email.available@business.subscription"
                )
            else:
                self.assertIn(type(field), available_data_types)

    def test_forward_compatibility(self):
        SearchAPIRequest.BASE_URL += "&show_unknown_fields=1"
        request = SearchAPIRequest(email="clark.kent@example.com")
        response = request.send()
        self.assertIsNotNone(response.person)

    def test_make_sure_insufficient_search_isnt_sent(self):
        request = SearchAPIRequest(first_name="brian")
        try:
            request.send()
            failed = False
        except Exception as e:
            failed = True
        self.assertTrue(failed)

    def test_make_sure_field_count_is_correct_on_premium(self):
        res = self.get_narrow_search_request().send()
        self.assertEqual(res.available_data.premium.relationships, 8)
        self.assertEqual(res.available_data.premium.usernames, 2)
        self.assertEqual(res.available_data.premium.jobs, 13)
        self.assertEqual(res.available_data.premium.addresses, 9)
        self.assertEqual(res.available_data.premium.phones, 4)
        self.assertEqual(res.available_data.premium.emails, 4)
        self.assertEqual(res.available_data.premium.languages, 1)
        self.assertEqual(res.available_data.premium.names, 1)
        self.assertEqual(res.available_data.premium.dobs, 1)
        self.assertEqual(res.available_data.premium.images, 2)
        self.assertEqual(res.available_data.premium.genders, 1)
        self.assertEqual(res.available_data.premium.educations, 2)
        self.assertEqual(res.available_data.premium.social_profiles, 3)

    def test_make_sure_field_count_is_correct_on_basic(self):
        SearchAPIRequest.BASE_URL = (
            os.getenv("API_TESTS_BASE_URL") + "?developer_class=social"
        )
        res = self.get_narrow_search_request().send()
        self.assertEqual(res.available_data.basic.relationships, 7)
        self.assertEqual(res.available_data.basic.usernames, 2)
        self.assertEqual(res.available_data.basic.jobs, 12)
        self.assertEqual(res.available_data.basic.addresses, 6)
        self.assertEqual(res.available_data.basic.phones, 1)
        self.assertEqual(res.available_data.basic.emails, 3)
        self.assertEqual(res.available_data.basic.user_ids, 4)
        self.assertEqual(res.available_data.basic.languages, 1)
        self.assertEqual(res.available_data.basic.names, 1)
        self.assertEqual(res.available_data.basic.dobs, 1)
        self.assertEqual(res.available_data.basic.images, 2)
        self.assertEqual(res.available_data.basic.genders, 1)
        self.assertEqual(res.available_data.basic.educations, 2)
        self.assertEqual(res.available_data.basic.social_profiles, 3)

    def test_response_class_default(self):
        request = SearchAPIRequest(email="clark.kent@example.com")
        response = request.send()
        self.assertIsInstance(response, SearchAPIResponse)

    def test_response_class_custom(self):
        custom_response_class = type("CustomResponseClass", (SearchAPIResponse,), {})
        request = SearchAPIRequest(
            email="clark.kent@example.com", response_class=custom_response_class
        )
        response = request.send()
        self.assertIsInstance(response, custom_response_class)
