import os
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import Tag, Video

TEMP_MEDIA = tempfile.mkdtemp()


class VideoListTests(TestCase):
    def test_filter_by_tag(self):
        demo = Tag.objects.create(name="demo")
        v1 = Video.objects.create(title="a", file="videos/a.mp4")
        Video.objects.create(title="b", file="videos/b.mp4")
        v1.tags.add(demo)

        response = self.client.get(reverse("video_list"), {"tag": "demo"})

        self.assertEqual(list(response.context["videos"]), [v1])

@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class DeleteVideoTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def make_video(self):
        return Video.objects.create(
            title="a.mp4", file=SimpleUploadedFile("a.mp4", b"data")
        )

    def test_delete_removes_record_and_file(self):
        video = self.make_video()
        path = video.file.path
        self.assertTrue(os.path.exists(path))

        response = self.client.post(reverse("delete", args=[video.pk]))

        self.assertRedirects(response, reverse("video_list"))
        self.assertFalse(Video.objects.filter(pk=video.pk).exists())
        self.assertFalse(os.path.exists(path))

    def test_delete_requires_post(self):
        video = self.make_video()

        response = self.client.get(reverse("delete", args=[video.pk]))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Video.objects.filter(pk=video.pk).exists())
