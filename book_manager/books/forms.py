from django import forms
from .models import Book

class BookForm(forms.ModelForm):
    SAVE_CHOICES = [
        ('db', 'Сохранить в базу данных'),
        ('file', 'Сохранить в файл'),
        ('both', 'Сохранить и в базу, и в файл'),
    ]
    
    save_location = forms.ChoiceField(
        choices=SAVE_CHOICES,
        widget=forms.RadioSelect(),
        initial='both',
        label='Куда сохранить данные?',
        required=True
    )
    
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'publication_year', 'genre', 'page_count', 'langua', 'description']
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название книги'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите автора'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ISBN (10 или 13 цифр)'}),
            'publication_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Год издания'}),
            'genre': forms.Select(attrs={'class': 'form-control'}),
            'page_count': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Количество страниц'}),
            'langua': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Язык книги'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Описание книги'}),
        }
        
        labels = {
            'title': 'Название книги',
            'author': 'Автор',
            'isbn': 'ISBN',
            'publication_year': 'Год издания',
            'genre': 'Жанр',
            'page_count': 'Количество страниц',
            'langua': 'Язык',
            'description': 'Описание',
        }

class FileUploadForm(forms.Form):
    file = forms.FileField(
        label='Файл для импорта',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    file_type = forms.ChoiceField(
        choices=[('json', 'JSON'), ('xml', 'XML')],
        widget=forms.RadioSelect(),
        initial='json',
        label='Тип файла'
    )