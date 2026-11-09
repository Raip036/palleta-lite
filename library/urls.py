from django.urls import path
from . import views

urlpatterns = [
    path("", views.video_list, name="video_list"),
    path("upload/", views.upload, name="upload"),
    path("download/<int:pk>/", views.download, name="download"),
    path("delete/<int:pk>/", views.delete_video, name="delete"),
]