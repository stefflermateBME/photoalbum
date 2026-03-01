from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("album.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
]

# In production OpenShift will still serve media from Django (OK for assignment).
# For real prod you'd use object storage or nginx.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)