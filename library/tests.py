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

    def test_delete_removes_tags_left_with_no_videos(self):
        video = self.make_video()
        video.tags.set([Tag.objects.create(name="solo")])

        self.client.post(reverse("delete", args=[video.pk]))

        self.assertFalse(Tag.objects.filter(name="solo").exists())

    def test_delete_keeps_tags_still_used_by_other_videos(self):
        shared = Tag.objects.create(name="shared")
        first = self.make_video()
        second = Video.objects.create(
            title="b.mp4", file=SimpleUploadedFile("b.mp4", b"data")
        )
        first.tags.set([shared])
        second.tags.set([shared])

        self.client.post(reverse("delete", args=[first.pk]))

        self.assertTrue(Tag.objects.filter(name="shared").exists())

    def test_delete_requires_post(self):
        video = self.make_video()

        response = self.client.get(reverse("delete", args=[video.pk]))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Video.objects.filter(pk=video.pk).exists())


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class UploadPreviewTests(TestCase):
    def upload(self, count=2, tags="demo"):
        files = [
            SimpleUploadedFile(f"clip{i}.mp4", b"data", content_type="video/mp4")
            for i in range(count)
        ]
        return self.client.post(reverse("upload"), {"files": files, "tags": tags})

    def test_success_screen_shows_previews_once(self):
        response = self.upload(count=2)
        # fetch_redirect_response=False: fetching the target would consume the session flag
        self.assertRedirects(response, reverse("upload"), fetch_redirect_response=False)

        page = self.client.get(reverse("upload"))
        self.assertEqual(page.context["uploaded_count"], 2)
        self.assertEqual(len(page.context["uploaded"]), 2)
        self.assertContains(page, "2 videos uploaded")

        # Refreshing must not show the success screen again
        again = self.client.get(reverse("upload"))
        self.assertNotIn("uploaded", again.context)

    def test_previews_are_capped(self):
        self.upload(count=8)
        page = self.client.get(reverse("upload"))
        self.assertEqual(len(page.context["uploaded"]), 6)
        self.assertEqual(page.context["uploaded_extra"], 2)
