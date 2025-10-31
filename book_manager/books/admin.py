from django.contrib import admin
from .models import Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'publication_year', 'genre', 'created_at']
    list_filter = ['genre', 'publication_year', 'created_at']
    search_fields = ['title', 'author', 'isbn']
    ordering = ['-created_at']