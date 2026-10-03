import uuid

from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Component(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="components")
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    thumbnail = models.ImageField(upload_to="components/", blank=True, null=True)
    thumbnail_url = models.URLField(max_length=1000, blank=True)
    thumbnail_source_url = models.URLField(max_length=1000, blank=True)
    thumbnail_credit = models.CharField(max_length=255, blank=True)
    specs = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["category__name", "name"]

    def __str__(self):
        return self.name


class Build(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        ORDERED = "ordered", "Оформлена"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="pc_builds",
    )
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    share_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class UserOrder(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Подтверждён"
        COMPLETED = "completed", "Завершён"
        CANCELLED = "cancelled", "Отменён"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pc_orders",
    )
    build = models.ForeignKey(Build, on_delete=models.PROTECT, related_name="orders")
    components = models.ManyToManyField(Component, through="UserOrderItem", related_name="pc_orders")
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_date = models.DateField()
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заказ №{self.pk} ({self.user})"


class UserOrderItem(models.Model):
    order = models.ForeignKey(UserOrder, on_delete=models.CASCADE, related_name="items")
    component = models.ForeignKey(
        Component,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    component_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.component_name} x {self.quantity}"


class BuildItem(models.Model):
    build = models.ForeignKey(Build, on_delete=models.CASCADE, related_name="items")
    component = models.ForeignKey(Component, on_delete=models.CASCADE, related_name="build_items")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("build", "component")

    def __str__(self):
        return f"{self.component} x {self.quantity}"