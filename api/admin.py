from django.contrib import admin

from api.models import Profile, TranslationJob

# Register your models here.
@admin.register(TranslationJob)
class TranslationJobAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "filename", "target_lang", "status", "created_at", "updated_at")
    list_filter = ("status", "target_lang", "created_at")
    search_fields = ("filename", "profile__user__username", "profile__user__email")
    ordering = ("-created_at",)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user"]
    search_fields = ("user__username", "user__email")