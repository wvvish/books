from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse
import re

def validate_isbn(value):
    """Валидация ISBN"""
    if value:
        # Удаляем дефисы и пробелы
        clean_isbn = re.sub(r'[-\s]', '', value)
        # Проверяем что это цифры и длина 10 или 13
        if not (clean_isbn.isdigit() and len(clean_isbn) in [10, 13]):
            raise ValidationError('ISBN должен содержать 10 или 13 цифр')
    return value

def validate_publication_year(value):
    """Валидация года публикации"""
    if value < 1000 or value > 2030:
        raise ValidationError('Год публикации должен быть между 1000 и 2030')
    return value

class Book(models.Model):
    GENRE_CHOICES = [
        ('fiction', 'Художественная литература'),
        ('non_fiction', 'Нехудожественная литература'),
        ('science', 'Научная литература'),
        ('fantasy', 'Фэнтези'),
        ('mystery', 'Детектив'),
        ('romance', 'Роман'),
        ('biography', 'Биография'),
        ('history', 'История'),
        ('other', 'Другое'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Название")
    author = models.CharField(max_length=100, verbose_name="Автор")
    isbn = models.CharField(max_length=17, verbose_name="ISBN", blank=True, null=True)
    publication_year = models.IntegerField(verbose_name="Год издания")
    genre = models.CharField(max_length=20, choices=GENRE_CHOICES, verbose_name="Жанр")
    publisher = models.CharField(max_length=100, verbose_name="Издательство", blank=True, null=True)
    page_count = models.IntegerField(verbose_name="Страниц", null=True, blank=True)
    description = models.TextField(verbose_name="Описание", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.author}"

    def get_absolute_url(self):
        return reverse('book_list')

    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"