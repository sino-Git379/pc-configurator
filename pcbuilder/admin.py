from django.contrib import admin

from .models import Build, BuildItem, Category, Component


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price")
    list_filter = ("category",)
    search_fields = ("name",)


class BuildItemInline(admin.TabularInline):
    model = BuildItem
    extra = 0


@admin.register(Build)
class BuildAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "created_at", "share_code")
    inlines = (BuildItemInline,)