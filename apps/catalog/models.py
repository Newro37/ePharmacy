from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Manufacturer(models.Model):
    name = models.CharField(max_length=200, unique=True)
    country = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return self.name

class MedicineQuerySet(models.QuerySet):
    """Repository Pattern: custom queryset provides chainable domain query methods."""
    def available(self):
        return self.filter(stock__gt=0, is_active=True)

    def by_category(self, category_slug):
        return self.filter(category__slug=category_slug, is_active=True)

    def low_stock(self, threshold=10):
        return self.filter(stock__lte=threshold, is_active=True)

    def search(self, query):
        from django.db.models import Q
        return self.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(manufacturer__name__icontains=query) |
            Q(dosage__icontains=query),
            is_active=True,
        )

class Medicine(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    dosage = models.CharField(max_length=100, blank=True, help_text='e.g., 500mg')
    side_effects = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='medicines')
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.SET_NULL, null=True, related_name='medicines')
    image = models.FileField(upload_to='medicines/', blank=True, null=True)
    prescription_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = MedicineQuerySet.as_manager()

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        return self.stock > 0

    def __str__(self):
        return f"{self.name} ({self.dosage}) - ৳{self.price}"
