from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("album.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
]

# In production OpenShift will still serve media from Django (OK for assignment).
# For real prod you'd use object storage or nginx.
# MEDIA kiszolgálás OKD-n (Gunicorn mögül)
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]