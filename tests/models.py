from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    author_id = models.IntegerField()

    class Meta:
        app_label = "tests"
