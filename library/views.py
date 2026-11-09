import os
import shutil
import tempfile
import zipfile
from urllib.parse import urlencode

from django.contrib import messages
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import EditVideoForm, UploadForm
from .models import Tag, Video

PREVIEW_LIMIT = 6


def video_list(request):
    videos = Video.objects.prefetch_related("tags")
    active_tag = request.GET.get("tag")
    if active_tag:
        videos = videos.filter(tags__name=active_tag)
    return render(request, "library/video_list.html", {
        "videos": videos,
        "tags": Tag.objects.all(),
        "active_tag": active_tag,
    })


def parse_tags(text):
    """'Lecture, demo,, lecture ' -> [Tag(lecture), Tag(demo)], creating tags as needed."""
    names = []
    for raw in text.split(","):
        name = raw.strip().lower()
        if name and name not in names:
            names.append(name)
    return [Tag.objects.get_or_create(name=n)[0] for n in names]


def is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def upload(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            tags = parse_tags(form.cleaned_data["tags"])
            created = []
            for f in form.cleaned_data["files"]:
                video = Video.objects.create(title=f.name, file=f)
                video.tags.set(tags)
                created.append(video.pk)
            # Post/Redirect/Get: remember what was uploaded for the success screen
            request.session["uploaded"] = created
            if is_ajax(request):
                # The browser's JS navigates here itself once the upload finishes
                return JsonResponse({"redirect": reverse("upload")})
            return redirect("upload")
        if is_ajax(request):
            errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
            return JsonResponse({"errors": errors}, status=400)
    else:
        form = UploadForm()

    context = {"form": form}
    ids = [] if request.method == "POST" else request.session.pop("uploaded", [])
    if ids:
        videos = list(Video.objects.filter(pk__in=ids).prefetch_related("tags"))
        videos.sort(key=lambda v: ids.index(v.pk))   # keep the order they were uploaded in
        context.update({
            "uploaded": videos[:PREVIEW_LIMIT],
            "uploaded_count": len(videos),
            "uploaded_extra": max(0, len(videos) - PREVIEW_LIMIT),
        })
    return render(request, "library/upload.html", context)


def download(request, pk):
    video = get_object_or_404(Video, pk=pk)
    return FileResponse(
        video.file.open("rb"),
        as_attachment=True,
        filename=os.path.basename(video.file.name),
    )

def selected_videos(request):
    """Videos whose ids were posted as ?ids=1&ids=2 (non-numbers are ignored)."""
    ids = [int(i) for i in request.POST.getlist("ids") if i.isdigit()]
    return Video.objects.filter(pk__in=ids)


def delete_videos(videos):
    """Delete videos, their files, and any tags left with no videos. Returns the count."""
    videos = list(videos)
    tag_ids = set(Tag.objects.filter(video__in=videos).values_list("pk", flat=True))
    for video in videos:
        video.file.delete(save=False)   # remove the file from storage, not just the DB row
        video.delete()
    Tag.objects.filter(pk__in=tag_ids, video__isnull=True).delete()
    return len(videos)


def back_to_library(request):
    """Stay on the current tag filter if it still has videos."""
    tag = request.POST.get("tag")
    if tag and Video.objects.filter(tags__name=tag).exists():
        return redirect(f"{reverse('video_list')}?{urlencode({'tag': tag})}")
    return redirect("video_list")


def unique_name(name, used):
    base, ext = os.path.splitext(name)
    candidate, n = name, 2
    while candidate in used:
        candidate = f"{base} ({n}){ext}"
        n += 1
    used.add(candidate)
    return candidate


@require_POST
def delete_video(request, pk):
    video = get_object_or_404(Video, pk=pk)
    title = video.title
    delete_videos([video])
    messages.success(request, f'Deleted "{title}".')
    return back_to_library(request)


@require_POST
def delete_selected(request):
    count = delete_videos(selected_videos(request))
    if count:
        messages.success(request, f"Deleted {count} video{'s' if count != 1 else ''}.")
    else:
        messages.error(request, "No videos were selected.")
    return back_to_library(request)


@require_POST
def download_selected(request):
    videos = list(selected_videos(request))
    if not videos:
        messages.error(request, "Select at least one video to download.")
        return back_to_library(request)

    # Build the ZIP in a temp file (not memory) and stream it back.
    # ZIP_STORED: video is already compressed, so deflating would only burn CPU.
    archive = tempfile.TemporaryFile()
    used = set()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_STORED) as zf:
        for video in videos:
            name = unique_name(os.path.basename(video.title) or "video", used)
            with video.file.open("rb") as src, zf.open(name, "w", force_zip64=True) as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
    archive.seek(0)
    return FileResponse(archive, as_attachment=True, filename="paletta-videos.zip")


def edit_video(request, pk):
    video = get_object_or_404(Video, pk=pk)
    if request.method == "POST":
        form = EditVideoForm(request.POST)
        if form.is_valid():
            old_tag_ids = set(video.tags.values_list("pk", flat=True))
            video.title = form.cleaned_data["title"]
            video.save(update_fields=["title"])
            video.tags.set(parse_tags(form.cleaned_data["tags"]))
            # Tags removed from this video may now be unused
            Tag.objects.filter(pk__in=old_tag_ids, video__isnull=True).delete()
            messages.success(request, f'Saved changes to "{video.title}".')
            return back_to_library(request)
    else:
        form = EditVideoForm(initial={
            "title": video.title,
            "tags": ", ".join(video.tags.values_list("name", flat=True)),
        })
    # Full-page fallback: used without JavaScript, or to show validation errors
    return render(request, "library/edit.html", {"form": form, "video": video})
