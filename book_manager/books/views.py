from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
import os
import json

from .models import Book
from .forms import BookForm, FileUploadForm
from .utils import FileHandler

def home(request):
    FileHandler.save_books_to_json()
    context = {
        'page': 'home',
        'books_count': Book.objects.count(),
        'files_count': len(FileHandler.get_all_files()),
    }
    return render(request, 'books/main.html', context)

def book_list(request):
    source = request.GET.get('source', 'db')
    query = request.GET.get('q', '')

    if source == 'file':
        books_data = FileHandler.load_books_from_json()
        books = []
        for book_data in books_data:
            class BookLikeObject:
                def __init__(self, data):
                    self.id = data.get('id')
                    self.title = data.get('title', '')
                    self.author = data.get('author', '')
                    self.isbn = data.get('isbn', '')
                    self.publication_year = data.get('publication_year')
                    self.genre = data.get('genre', 'other')
                    self.langua = data.get('langua', 'Русский')
                    self.page_count = data.get('page_count')
                    self.description = data.get('description', '')
                    self.created_at = data.get('created_at')
                
                def get_genre_display(self):
                    genre_dict = dict(Book.GENRE_CHOICES)
                    return genre_dict.get(self.genre, self.genre)
            
            books.append(BookLikeObject(book_data))
        
        if query:
            books = [b for b in books if query.lower() in b.title.lower() or query.lower() in b.author.lower()]
        
        books.sort(key=lambda x: x.created_at if x.created_at else '', reverse=True)
    else:
        if query:
            books = Book.objects.filter(
                Q(title__icontains=query) | 
                Q(author__icontains=query) |
                Q(description__icontains=query)
            ).order_by('-created_at')
        else:
            books = Book.objects.all().order_by('-created_at')
        
        FileHandler.save_books_to_json()
    
    paginator = Paginator(books, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page': 'book_list',
        'page_obj': page_obj,
        'books_count': len(books) if source == 'file' else books.count(),
        'current_source': source,
        'search_query': query
    }
    return render(request, 'books/main.html', context)

def search_books_ajax(request):
    """AJAX поиск книг - возвращает JSON"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('q', '')
        if query:
            books = Book.objects.filter(
                Q(title__icontains=query) | 
                Q(author__icontains=query) |
                Q(description__icontains=query)
            )[:10]
            
            results = []
            for book in books:
                results.append({
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'publication_year': book.publication_year,
                    'genre': book.get_genre_display(),
                    'langua': book.langua,
                    'edit_url': f"/books/{book.id}/edit/",
                    'delete_url': f"/books/{book.id}/delete/"
                })
            
            return JsonResponse(results, safe=False)
    
    return JsonResponse([], safe=False)

def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            save_location = form.cleaned_data['save_location']
            
            # Для варианта "только файл" - временно сохраняем в БД, потом удаляем
            temp_book = None
            if save_location == 'file':
                # Сохраняем во временную БД чтобы потом экспортировать в файл
                temp_book = form.save()
                # Сохраняем все книги (включая новую) в файл
                FileHandler.save_books_to_json()
                # Удаляем временную книгу из БД
                temp_book.delete()
                messages.success(request, 'Книга сохранена в файл!')
                
            elif save_location == 'db':
                # Проверка на дубликаты для БД
                duplicate = Book.objects.filter(
                    title=form.cleaned_data['title'],
                    author=form.cleaned_data['author'],
                    publication_year=form.cleaned_data['publication_year']
                ).exists()
                
                if duplicate:
                    messages.error(request, 'Такая книга уже существует в базе данных!')
                    return render(request, 'books/main.html', {'page': 'add_book', 'form': form})
                
                book = form.save()
                messages.success(request, f'Книга "{book.title}" сохранена в базу данных!')
                
            elif save_location == 'both':
                # Проверка на дубликаты
                duplicate = Book.objects.filter(
                    title=form.cleaned_data['title'],
                    author=form.cleaned_data['author'], 
                    publication_year=form.cleaned_data['publication_year']
                ).exists()
                
                if duplicate:
                    messages.error(request, 'Такая книга уже существует в базе данных!')
                    return render(request, 'books/main.html', {'page': 'add_book', 'form': form})
                
                book = form.save()
                FileHandler.save_books_to_json()
                messages.success(request, f'Книга "{book.title}" сохранена и в базу, и в файл!')
            
            return redirect('book_list')
        else:
            context = {'page': 'add_book', 'form': form}
            return render(request, 'books/main.html', context)
    else:
        form = BookForm()
    
    context = {'page': 'add_book', 'form': form}
    return render(request, 'books/main.html', context)

def edit_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            FileHandler.save_books_to_json()
            messages.success(request, f'Книга "{book.title}" успешно обновлена!')
            return redirect('book_list')
        else:
            context = {'page': 'edit_book', 'form': form, 'book': book}
            return render(request, 'books/main.html', context)
    else:
        form = BookForm(instance=book)
        form.fields.pop('save_location', None)
    
    context = {'page': 'edit_book', 'form': form, 'book': book}
    return render(request, 'books/main.html', context)

def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        book_title = book.title
        book.delete()
        FileHandler.save_books_to_json()
        messages.success(request, f'Книга "{book_title}" успешно удалена!')
        return redirect('book_list')
    
    context = {'page': 'delete_book', 'book': book}
    return render(request, 'books/main.html', context)

def export_books(request):
    if request.method == 'POST':
        file_type = request.POST.get('file_type')
        
        try:
            if file_type == 'json':
                file_path = FileHandler.save_books_to_json()
                content_type = 'application/json'
                filename = 'books.json'
            else:
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
                content = file.read().decode('utf-8')
                
                if file_type == 'json':
                    books_data = json.loads(content)
                else:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(content)
                    books_data = []
                    for book_elem in root.findall('book'):
                        book_data = {}
                        for child in book_elem:
                            book_data[child.tag] = child.text
                        books_data.append(book_data)
                
                imported_count = 0
                for book_data in books_data:
                    Book.objects.create(
                        title=book_data['title'],
                        author=book_data['author'],
                        isbn=book_data.get('isbn', ''),
                        publication_year=int(book_data['publication_year']),
                        genre=book_data.get('genre', 'other'),
                        langua=book_data.get('langua', 'Русский'),
                        page_count=book_data.get('page_count'),
                        description=book_data.get('description', ''),
                    )
                    imported_count += 1
                
                FileHandler.save_books_to_json()
                messages.success(request, f'Импортировано {imported_count} книг!')
                
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
            
            return redirect('upload_file')
        else:
            context = {'page': 'upload_file', 'form': form}
            return render(request, 'books/main.html', context)
    else:
        form = FileUploadForm()
    
    context = {'page': 'upload_file', 'form': form}
    return render(request, 'books/main.html', context)

def file_list(request):
    files = FileHandler.get_all_files()
    
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