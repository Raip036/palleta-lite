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


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class AjaxUploadTests(TestCase):
    AJAX = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}

    def test_ajax_upload_returns_redirect_json(self):
        files = [SimpleUploadedFile("a.mp4", b"data", content_type="video/mp4")]
        response = self.client.post(reverse("upload"), {"files": files}, **self.AJAX)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"redirect": reverse("upload")})
        self.assertEqual(Video.objects.count(), 1)

    def test_ajax_upload_without_files_returns_errors(self):
        response = self.client.post(reverse("upload"), {"tags": "x"}, **self.AJAX)

        self.assertEqual(response.status_code, 400)
        self.assertIn("files", response.json()["errors"])


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class SelectedVideoTests(TestCase):
    def make(self, title, data=b"data"):
        return Video.objects.create(title=title, file=SimpleUploadedFile(title, data))

    def test_download_selected_returns_zip_of_chosen_videos(self):
        import io, zipfile
        a = self.make("a.mp4", b"AAA")
        b = self.make("b.mp4", b"BBB")
        self.make("c.mp4")   # not selected

        response = self.client.post(reverse("download_selected"), {"ids": [a.pk, b.pk]})

        self.assertEqual(response.status_code, 200)
        self.assertIn("paletta-videos.zip", response["Content-Disposition"])
        archive = zipfile.ZipFile(io.BytesIO(b"".join(response.streaming_content)))
        self.assertEqual(sorted(archive.namelist()), ["a.mp4", "b.mp4"])
        self.assertEqual(archive.read("a.mp4"), b"AAA")

    def test_zip_renames_duplicate_titles(self):
        import io, zipfile
        a = self.make("clip.mp4")
        b = self.make("clip.mp4")

        response = self.client.post(reverse("download_selected"), {"ids": [a.pk, b.pk]})

        archive = zipfile.ZipFile(io.BytesIO(b"".join(response.streaming_content)))
        self.assertEqual(sorted(archive.namelist()), ["clip (2).mp4", "clip.mp4"])

    def test_download_selected_with_nothing_selected_redirects(self):
        response = self.client.post(reverse("download_selected"), {})
        self.assertRedirects(response, reverse("video_list"))

    def test_delete_selected_removes_only_chosen_videos_and_orphan_tags(self):
        lone = Tag.objects.create(name="lone")
        shared = Tag.objects.create(name="shared")
        a = self.make("a.mp4")
        b = self.make("b.mp4")
        keep = self.make("keep.mp4")
        a.tags.set([lone, shared])
        b.tags.set([lone])
        keep.tags.set([shared])
        paths = [a.file.path, b.file.path]

        self.client.post(reverse("delete_selected"), {"ids": [a.pk, b.pk]})

        self.assertEqual(list(Video.objects.all()), [keep])
        self.assertFalse(any(os.path.exists(p) for p in paths))
        self.assertFalse(Tag.objects.filter(name="lone").exists())
        self.assertTrue(Tag.objects.filter(name="shared").exists())

    def test_bulk_endpoints_require_post(self):
        self.assertEqual(self.client.get(reverse("download_selected")).status_code, 405)
        self.assertEqual(self.client.get(reverse("delete_selected")).status_code, 405)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class EditVideoTests(TestCase):
    def setUp(self):
        self.video = Video.objects.create(
            title="old.mp4", file=SimpleUploadedFile("old.mp4", b"data")
        )

    def test_edit_updates_title_and_tags(self):
        response = self.client.post(
            reverse("edit", args=[self.video.pk]),
            {"title": "  Week 1 lecture ", "tags": "Lecture, demo, lecture"},
        )

        self.assertRedirects(response, reverse("video_list"))
        self.video.refresh_from_db()
        self.assertEqual(self.video.title, "Week 1 lecture")
        self.assertEqual(
            sorted(self.video.tags.values_list("name", flat=True)), ["demo", "lecture"]
        )

    def test_removing_a_tag_deletes_it_only_if_unused(self):
        lone = Tag.objects.create(name="lone")
        shared = Tag.objects.create(name="shared")
        other = Video.objects.create(title="b.mp4", file=SimpleUploadedFile("b.mp4", b"data"))
        self.video.tags.set([lone, shared])
        other.tags.set([shared])

        self.client.post(reverse("edit", args=[self.video.pk]), {"title": "old.mp4", "tags": ""})

        self.assertFalse(Tag.objects.filter(name="lone").exists())
        self.assertTrue(Tag.objects.filter(name="shared").exists())

    def test_blank_title_is_rejected(self):
        response = self.client.post(reverse("edit", args=[self.video.pk]), {"title": "   ", "tags": ""})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["title"])
        self.video.refresh_from_db()
        self.assertEqual(self.video.title, "old.mp4")

    def test_edit_page_is_prefilled(self):
        self.video.tags.set([Tag.objects.create(name="demo")])

        response = self.client.get(reverse("edit", args=[self.video.pk]))

        self.assertEqual(response.context["form"].initial["tags"], "demo")
        self.assertContains(response, 'value="old.mp4"')
