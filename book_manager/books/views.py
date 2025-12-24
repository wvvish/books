from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
import os
import json
import random
from datetime import datetime

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

from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from .utils import FileHandler

@csrf_exempt
def search_books_ajax(request):
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400) #некорректный запрос - ошибка
    
    # q - Ключ, по которому извлекается значение из request.GET
    query = request.GET.get('q', '').strip() # Получаем поисковый запрос, убираем пробелы

    # Если запрос слишком короткий
    if len(query) < 2:
        return JsonResponse([], safe=False) # Возвращаем пустой список
    
    # Для всех найденных книг
    results = []

    
    # начало блока обработки исключений в Python.
    try:
        # Поиск в базе данных
        db_books = Book.objects.filter( # Cтандартный способ фильтрации записей в Django.
            Q(title__icontains=query) | 
            Q(author__icontains=query) |
            Q(description__icontains=query) |
            Q(isbn__icontains=query) |
            Q(genre__icontains=query) |
            Q(langua__icontains=query)
        )[:10]  # Ограничиваем 10 результатами из БД

        # Преобразует найденные книги из бд с нужными полями 
        for book in db_books:
            results.append({
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'publication_year': book.publication_year,
                'genre': book.get_genre_display(),
                'langua': book.langua or '',
                'edit_url': f"/books/{book.id}/edit/", # даёт путь вида, по которому отправляется запрос, чтобы открыть форму редактирования книги
                'delete_url': f"/books/{book.id}/delete/",
                'source': 'db'
            })

        # 2. Поиск в файле
        try:
            books_from_file = FileHandler.load_books_from_json() 
            # load_books_from_json() — статический или классовый метод, открывает json файл, читает и возвращает

            for book_data in books_from_file:
                # Проверяем совпадения 
                # Получает значение по ключу титл
                title_match = query.lower() in str(book_data.get('title', '')).lower()
                author_match = query.lower() in str(book_data.get('author', '')).lower()

                # Если совпадают один из них:
                if title_match or author_match:
                    genre = book_data.get('genre', 'other')
                    # Если его нет — используем 'other' (значение по умолчанию)
                    # Преобразует список в словарь, преобразуем внутреннее значение жанра (например, "fantasy") в читаемое название 
                    genre_display = dict(Book.GENRE_CHOICES).get(genre, genre)

                    # Получаем id книги из json
                    book_id = book_data.get('id', 0)
                    # Добавляем новую карточку книги в общий список результатов
                    results.append({
                        'id': book_id,
                        'title': book_data.get('title', ''),
                        'author': book_data.get('author', ''),
                        'publication_year': book_data.get('publication_year', ''),
                        'genre': genre_display,
                        'langua': book_data.get('langua', ''),
                        'edit_url': f"/books/{book_id}/edit/" if book_id else '#',
                        'delete_url': f"/books/{book_id}/delete/" if book_id else '#',
                        'source': 'file'
                    })

                    if len(results) >= 15:  # Общее ограничение
                        break

        except Exception as e:
            print(f"Ошибка при поиске в файле: {e}")
            # Продолжаем работу

    except Exception as e:
        print(f"Ошибка в поиске: {e}")
        return JsonResponse([], safe=False)
    
    # Отправляет первые 15 найденных книг в формате JSON
    return JsonResponse(results[:15], safe=False)  

def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            save_location = form.cleaned_data['save_location']

            if save_location == 'file':
                # Сохраняем только в файл
                file_path = FileHandler.get_json_file_path()
                existing_books = FileHandler.load_books_from_json()

                new_book = {
                    'id': random.randint(1000, 9999),
                    'title': form.cleaned_data['title'],
                    'author': form.cleaned_data['author'],
                    'isbn': form.cleaned_data['isbn'],
                    'publication_year': form.cleaned_data['publication_year'],
                    'genre': form.cleaned_data['genre'],
                    'langua': form.cleaned_data['langua'],
                    'page_count': form.cleaned_data['page_count'],
                    'description': form.cleaned_data['description'],
                    'created_at': datetime.now().isoformat(),
                }

                existing_books.append(new_book)

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_books, f, ensure_ascii=False, indent=2)

                messages.success(request, 'Книга сохранена в файл!')

            elif save_location == 'db':
                # Сохраняем только в БД
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
                # Сохраняем в оба места
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