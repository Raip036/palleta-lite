import os
from urllib.parse import urlencode

from django.contrib import messages
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import UploadForm
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


def is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def upload(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            names = [
                t.strip().lower()
                for t in form.cleaned_data["tags"].split(",")
                if t.strip()
            ]
            tags = [Tag.objects.get_or_create(name=n)[0] for n in names]
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

@require_POST
def delete_video(request, pk):
    video = get_object_or_404(Video, pk=pk)
    title = video.title
    tag_ids = list(video.tags.values_list("pk", flat=True))
    video.file.delete(save=False)   # remove the file from storage, not just the DB row
    video.delete()
    # Remove tags this video was the last user of, so empty tags don't linger
    Tag.objects.filter(pk__in=tag_ids, video__isnull=True).delete()
    messages.success(request, f'Deleted "{title}".')

    # Stay on the current tag filter if it still has videos
    tag = request.POST.get("tag")
    if tag and Video.objects.filter(tags__name=tag).exists():
        return redirect(f"{reverse('video_list')}?{urlencode({'tag': tag})}")
    return redirect("video_list")
