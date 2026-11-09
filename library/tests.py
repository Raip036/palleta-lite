from django.test import TestCase
from django.urls import reverse
from .models import Tag, Video


class VideoListTests(TestCase):
    def test_filter_by_tag(self):
        demo = Tag.objects.create(name="demo")
        v1 = Video.objects.create(title="a", file="videos/a.mp4")
        Video.objects.create(title="b", file="videos/b.mp4")
        v1.tags.add(demo)

        response = self.client.get(reverse("video_list"), {"tag": "demo"})

        self.assertEqual(list(response.context["videos"]), [v1])