from django.contrib import admin

from interface.models import Commit, Repo


@admin.register(Repo)
class RepoAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'is_private', 'created_at')

    class Meta:
        model = Repo


@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    list_display = ('short_sha', 'ref', 'get_full_name', 'status', 'created_at')

    def get_full_name(self, obj):
        return obj.repo.full_name

    get_full_name.short_description = 'Repo'
    get_full_name.admin_order_field = 'repo__full_name'

    class Meta:
        model = Commit
