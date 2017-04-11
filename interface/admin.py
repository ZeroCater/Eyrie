from django.contrib import admin

from interface.models import Repo


@admin.register(Repo)
class RepoAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'is_private', 'created_at')

    class Meta:
        model = Repo
