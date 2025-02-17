from django.db import models

class Country(models.Model):

    name = models.CharField(max_length=100, unique=True, verbose_name="Название страны")
    image_country = models.ImageField(upload_to="image_counties/", blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Страна"
        verbose_name_plural = "Страны"
