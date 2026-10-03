from django.contrib import admin

from .models import Build, BuildItem, Category, Component, UserOrder, UserOrderItem


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


class UserOrderItemInline(admin.TabularInline):
    model = UserOrderItem
    extra = 0
    readonly_fields = ("component_name", "unit_price", "quantity")


@admin.register(UserOrder)
class UserOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_price", "delivery_date", "status", "created_at")
    list_filter = ("status", "delivery_date", "created_at")
    readonly_fields = ("user", "build", "total_price", "delivery_date", "email", "created_at")
    inlines = (UserOrderItemInline,)