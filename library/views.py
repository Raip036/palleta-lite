import os
from urllib.parse import urlencode

from django.contrib import messages
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import UploadForm
from .models import Tag, Video


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
            files = form.cleaned_data["files"]
            for f in files:
                video = Video.objects.create(title=f.name, file=f)
                video.tags.set(tags)
            messages.success(
                request,
                f"Uploaded {len(files)} video{'s' if len(files) != 1 else ''}.",
            )
            return redirect("video_list")
    else:
        form = UploadForm()
    return render(request, "library/upload.html", {"form": form})


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
    video.file.delete(save=False)   # remove the file from storage, not just the DB row
    video.delete()
    messages.success(request, f'Deleted "{title}".')

    # Stay on the current tag filter if it still has videos
    tag = request.POST.get("tag")
    if tag and Video.objects.filter(tags__name=tag).exists():
        return redirect(f"{reverse('video_list')}?{urlencode({'tag': tag})}")
    return redirect("video_list")
