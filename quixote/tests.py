# sancho/tests.py
import pytest
from django.test import SimpleTestCase
from django.urls import reverse

class HomepageTests(SimpleTestCase):
    def test_url_exists_at_correct_location(self):
        response = self.client.get("/")
        assert response.status_code == 200
    
    def test_url_available_by_name(self):
        response = self.client.get(reverse("home"))
        assert response.status_code == 200
        
@pytest.mark.xfail(reason='About page in project folders')        
class AboutpageTests(SimpleTestCase):
    def test_url_exists_at_correct_location(self):
        response = self.client.get("about/")
        assert response.status_code == 200
    
    def test_url_available_by_name(self):
        response = self.client.get(reverse("about"))
        assert response.status_code == 200
        
