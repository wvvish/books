import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import uuid
from django.conf import settings

class FileHandler:
    @staticmethod
    def get_data_path():
        data_dir = os.path.join(settings.BASE_DIR, 'data')
        os.makedirs(data_dir, exist_ok=True)
        return data_dir

    @staticmethod
    def get_json_file_path():
        return os.path.join(FileHandler.get_data_path(), 'books.json')

    @staticmethod
    def save_books_to_json(books_data=None):
        if books_data is None:
            from .models import Book
            books = Book.objects.all()
            books_data = []
            for book in books:
                books_data.append({
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'isbn': book.isbn,
                    'publication_year': book.publication_year,
                    'genre': book.genre,
                    'langua': book.langua,
                    'page_count': book.page_count,
                    'description': book.description,
                    'created_at': book.created_at.isoformat(),
                })
        
        file_path = FileHandler.get_json_file_path()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(books_data, f, ensure_ascii=False, indent=2)
        
        return file_path

    @staticmethod
    def load_books_from_json():
        file_path = FileHandler.get_json_file_path()
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    @staticmethod
    def export_to_xml():
        from .models import Book
        books = Book.objects.all()
        books_data = []
        for book in books:
            books_data.append({
                'title': book.title,
                'author': book.author,
                'isbn': book.isbn,
                'publication_year': book.publication_year,
                'genre': book.genre,
                'langua': book.langua,
                'page_count': book.page_count,
                'description': book.description,
            })
        
        data_dir = FileHandler.get_data_path()
        file_path = os.path.join(data_dir, f'books_export_{uuid.uuid4().hex[:8]}.xml')
        
        root = ET.Element('books')
        for book_data in books_data:
            book_elem = ET.SubElement(root, 'book')
            for key, value in book_data.items():
                if value is not None:
                    child = ET.SubElement(book_elem, key)
                    child.text = str(value)
        
        xml_str = ET.tostring(root, encoding='utf-8')
        parsed_xml = minidom.parseString(xml_str)
        pretty_xml = parsed_xml.toprettyxml(indent="  ")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        return file_path

    @staticmethod
    def get_all_files():
        data_dir = FileHandler.get_data_path()
        files = []
        if os.path.exists(data_dir):
            for filename in os.listdir(data_dir):
                if filename.endswith(('.json', '.xml')):
                    file_path = os.path.join(data_dir, filename)
                    files.append({
                        'name': filename,
                        'path': file_path,
                        'size': os.path.getsize(file_path),
                    })
        return files