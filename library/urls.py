from django.urls import path
from . import views

urlpatterns = [
    path("", views.video_list, name="video_list"),
    path("upload/", views.upload, name="upload"),
    path("download/<int:pk>/", views.download, name="download"),
    path("edit/<int:pk>/", views.edit_video, name="edit"),
    path("delete/<int:pk>/", views.delete_video, name="delete"),
    path("selected/download/", views.download_selected, name="download_selected"),
    path("selected/delete/", views.delete_selected, name="delete_selected"),
]