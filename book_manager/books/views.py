from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
import os
import json

from .models import Book
from .forms import BookForm, FileUploadForm
from .utils import FileHandler

def home(request):
    # Автоматически сохраняем книги в JSON при загрузке главной страницы
    FileHandler.save_books_to_json()
    
    context = {
        'page': 'home',
        'books_count': Book.objects.count(),
        'files_count': len(FileHandler.get_all_files()),
    }
    return render(request, 'books/main.html', context)

def book_list(request):
    books = Book.objects.all().order_by('-created_at')
    
    # Сохраняем в JSON при просмотре списка
    FileHandler.save_books_to_json()
    
    paginator = Paginator(books, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page': 'book_list',
        'page_obj': page_obj,
        'books_count': books.count()
    }
    return render(request, 'books/main.html', context)

def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save()
            
            # СОХРАНЯЕМ В JSON ПОСЛЕ ДОБАВЛЕНИЯ КНИГИ
            FileHandler.save_books_to_json()
            
            messages.success(request, f'Книга "{book.title}" добавлена и сохранена в JSON!')
            return redirect('book_list')
    else:
        form = BookForm()
    
    context = {
        'page': 'add_book',
        'form': form
    }
    return render(request, 'books/main.html', context)

def edit_book(request, book_id):
    """Редактировать книгу"""
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            
            # Обновляем JSON файл после редактирования
            FileHandler.save_books_to_json()
            
            messages.success(request, f'Книга "{book.title}" успешно обновлена!')
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    
    context = {
        'page': 'edit_book',
        'form': form,
        'book': book
    }
    return render(request, 'books/main.html', context)

def delete_book(request, book_id):
    """Удалить книгу"""
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        book_title = book.title
        book.delete()
        
        # Обновляем JSON файл после удаления
        FileHandler.save_books_to_json()
        
        messages.success(request, f'Книга "{book_title}" успешно удалена!')
        return redirect('book_list')
    
    # Если GET запрос, показываем страницу подтверждения
    context = {
        'page': 'delete_book',
        'book': book
    }
    return render(request, 'books/main.html', context)

def export_books(request):
    if request.method == 'POST':
        file_type = request.POST.get('file_type')
        
        try:
            if file_type == 'json':
                file_path = FileHandler.save_books_to_json()
                content_type = 'application/json'
                filename = 'books.json'
            else:  # xml
                file_path = FileHandler.export_to_xml()
                content_type = 'application/xml'
                filename = os.path.basename(file_path)
            
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type=content_type)
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
                
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
    
    context = {
        'page': 'export_books',
        'books_count': Book.objects.count()
    }
    return render(request, 'books/main.html', context)

def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            file_type = form.cleaned_data['file_type']
            
            try:
                # Читаем файл
                content = file.read().decode('utf-8')
                
                if file_type == 'json':
                    books_data = json.loads(content)
                else:
                    # Для XML потребуется парсинг (упрощенная версия)
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(content)
                    books_data = []
                    for book_elem in root.findall('book'):
                        book_data = {}
                        for child in book_elem:
                            book_data[child.tag] = child.text
                        books_data.append(book_data)
                
                # Сохраняем книги в базу
                imported_count = 0
                for book_data in books_data:
                    Book.objects.create(
                        title=book_data['title'],
                        author=book_data['author'],
                        isbn=book_data.get('isbn', ''),
                        publication_year=int(book_data['publication_year']),
                        genre=book_data.get('genre', 'other'),
                        publisher=book_data.get('publisher', ''),
                        page_count=book_data.get('page_count'),
                        description=book_data.get('description', '')
                    )
                    imported_count += 1
                
                # Сохраняем в JSON после импорта
                FileHandler.save_books_to_json()
                
                messages.success(request, f'Импортировано {imported_count} книг!')
                
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
            
            return redirect('upload_file')
    else:
        form = FileUploadForm()
    
    context = {
        'page': 'upload_file',
        'form': form
    }
    return render(request, 'books/main.html', context)

def file_list(request):
    files = FileHandler.get_all_files()
    
    # Читаем содержимое файлов для предпросмотра
    for file_info in files:
        try:
            with open(file_info['path'], 'r', encoding='utf-8') as f:
                content = f.read()
                file_info['preview'] = content[:200] + '...' if len(content) > 200 else content
        except:
            file_info['preview'] = 'Не удалось прочитать файл'
    
    context = {
        'page': 'file_list',
        'files': files,
        'files_count': len(files)
    }
    return render(request, 'books/main.html', context)

def view_file(request, filename):
    data_dir = FileHandler.get_data_path()
    file_path = os.path.join(data_dir, filename)
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        context = {
            'page': 'view_file',
            'filename': filename,
            'content': content
        }
        return render(request, 'books/main.html', context)
    else:
        messages.error(request, 'Файл не найден')
        return redirect('file_list')