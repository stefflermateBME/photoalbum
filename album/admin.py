from django.contrib import admin
from .models import Photo

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "uploaded_at")
    search_fields = ("name", "owner__username")
    list_filter = ("uploaded_at",)