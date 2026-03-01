from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import PhotoUploadForm
from .models import Photo


def photo_list(request):
    sort = request.GET.get("sort", "date")

    qs = Photo.objects.all().select_related("owner")
    if sort == "name":
        qs = qs.order_by("name", "-uploaded_at")
    else:
        qs = qs.order_by("-uploaded_at")

    return render(request, "album/photo_list.html", {"photos": qs, "sort": sort})


def photo_detail(request, pk: int):
    photo = get_object_or_404(Photo, pk=pk)
    return render(request, "album/photo_detail.html", {"photo": photo})


@login_required
def photo_upload(request):
    if request.method == "POST":
        form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.owner = request.user
            photo.save()
            return redirect("photo-list")
    else:
        form = PhotoUploadForm()

    return render(request, "album/photo_upload.html", {"form": form})


@login_required
def photo_delete(request, pk: int):
    photo = get_object_or_404(Photo, pk=pk)

    if photo.owner != request.user:
        return HttpResponseForbidden("Csak a saját képedet törölheted.")

    if request.method == "POST":
        photo.image.delete(save=False)  # file from storage (PVC)
        photo.delete()
        return redirect("photo-list")

    return render(request, "album/photo_confirm_delete.html", {"photo": photo})

# build trigger test 333 ADSl
def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("photo-list")
    else:
        form = UserCreationForm()

    return render(request, "registration/signup.html", {"form": form})