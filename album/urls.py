from django.urls import path
from . import views

urlpatterns = [
    path("", views.photo_list, name="photo-list"),
    path("photos/<int:pk>/", views.photo_detail, name="photo-detail"),
    path("upload/", views.photo_upload, name="photo-upload"),
    path("photos/<int:pk>/delete/", views.photo_delete, name="photo-delete"),
    path("signup/", views.signup, name="signup"),
]