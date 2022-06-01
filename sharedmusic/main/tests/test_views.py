from django.test import RequestFactory, TestCase
from main.models import CustomUser, Room, RoomPlaylist
from main.views import HomeView


class ViewsTestCase(TestCase):

    def setUp(self):
        self.host = CustomUser.objects.create(username="test1", password="112345Aa")

    def test_homeview_form_valid(self):
        self.assertEqual(Room.objects.count(), 0)
        self.assertEqual(RoomPlaylist.objects.count(), 0)
        factory = RequestFactory()
        request = factory.post('/', data={})
        request.user = self.host
        HomeView.as_view()(request)
        self.assertEqual(Room.objects.count(), 1)
        self.assertEqual(RoomPlaylist.objects.count(), 1)
        self.assertEqual(Room.objects.first().host, self.host)
