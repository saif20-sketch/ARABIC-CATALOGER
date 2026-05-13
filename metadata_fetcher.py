import requests
import re
import os
from typing import Dict, List, Optional

class EnhancedMetadataFetcher:
    """مسترد محسن للبيانات الوصفية من مصادر متعددة"""
    
    def __init__(self):
        self.sources = [
            self._fetch_google_books,
            self._fetch_openlibrary,
            self._fetch_isbndb,
            self._fetch_worldcat
        ]
    
    def fetch_metadata(self, isbn: str) -> Dict:
        """استرجاع البيانات الوصفية من جميع المصادر"""
        all_results = []
        for source_func in self.sources:
            try:
                result = source_func(isbn)
                if result and result.get('title'):
                    all_results.append(result)
            except Exception:
                continue
        if not all_results:
            return self._get_empty_metadata(isbn)
        return self._merge_results(all_results, isbn)
    
    def _fetch_google_books(self, isbn: str) -> Optional[Dict]:
        """استرجاع من Google Books API"""
        try:
            url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and len(data['items']) > 0:
                    volume_info = data['items'][0]['volumeInfo']
                    published_date = self._extract_date(volume_info.get('publishedDate', ''))
                    return {
                        'source': 'Google Books',
                        'title': volume_info.get('title', ''),
                        'authors': volume_info.get('authors', []),
                        'publisher': volume_info.get('publisher', ''),
                        'published_date': published_date,
                        'description': volume_info.get('description', ''),
                        'page_count': volume_info.get('pageCount'),
                        'categories': volume_info.get('categories', []),
                        'language': volume_info.get('language', 'en'),
                        'isbn_10': self._extract_isbn(volume_info.get('industryIdentifiers', []), 'ISBN_10'),
                        'isbn_13': self._extract_isbn(volume_info.get('industryIdentifiers', []), 'ISBN_13'),
                        'edition': volume_info.get('edition', ''),  # ✅ حقل الطبعة
                        'confidence': 'high'
                    }
        except:
            pass
        return None
    
    def _fetch_openlibrary(self, isbn: str) -> Optional[Dict]:
        """استرجاع من OpenLibrary API"""
        try:
            url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if f'ISBN:{isbn}' in data:
                    book_data = data[f'ISBN:{isbn}']
                    publish_date = self._extract_date(book_data.get('publish_date', ''))
                    edition_info = book_data.get('edition_name', '') or book_data.get('edition', '')
                    return {
                        'source': 'OpenLibrary',
                        'title': book_data.get('title', ''),
                        'authors': [author.get('name') for author in book_data.get('authors', [])],
                        'publishers': [pub.get('name') for pub in book_data.get('publishers', [])],
                        'published_date': publish_date,
                        'subjects': [subj.get('name') for subj in book_data.get('subjects', [])],
                        'number_of_pages': book_data.get('number_of_pages'),
                        'edition': edition_info,  # ✅ حقل الطبعة
                        'confidence': 'medium'
                    }
        except:
            pass
        return None
    
    def _fetch_isbndb(self, isbn: str) -> Optional[Dict]:
        """استرجاع من ISBNdb (يتطلب مفتاح API)"""
        api_key = os.getenv('ISBNDB_KEY')
        if not api_key:
            return None
        try:
            url = f"https://api.isbndb.com/book/{isbn}"
            headers = {'Authorization': api_key}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'book' in data:
                    book = data['book']
                    return {
                        'source': 'ISBNdb',
                        'title': book.get('title', ''),
                        'authors': book.get('authors', []),
                        'publisher': book.get('publisher', ''),
                        'published_date': book.get('date_published', ''),
                        'synopsis': book.get('synopsis', ''),
                        'pages': book.get('pages', ''),
                        'edition': book.get('edition', ''),  # ✅ حقل الطبعة
                        'confidence': 'high'
                    }
        except:
            pass
        return None
    
    def _fetch_worldcat(self, isbn: str) -> Optional[Dict]:
        """استرجاع من WorldCat (يتطلب مفتاح API)"""
        api_key = os.getenv('WORLDCAT_KEY')
        if not api_key:
            return None
        try:
            url = f"http://www.worldcat.org/webservices/catalog/content/isbn/{isbn}?wskey={api_key}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text
                title_match = re.search(r'<title>([^<]+)</title>', content)
                title = title_match.group(1) if title_match else ''
                author_match = re.search(r'<author>([^<]+)</author>', content)
                author = author_match.group(1) if author_match else ''
                date_match = re.search(r'<date>([^<]+)</date>', content)
                date = date_match.group(1) if date_match else ''
                if title:
                    return {
                        'source': 'WorldCat',
                        'title': title,
                        'authors': [author] if author else [],
                        'published_date': self._extract_date(date),
                        'edition': '',  # WorldCat لا يوفر الطبعة بسهولة
                        'confidence': 'medium'
                    }
        except:
            pass
        return None
    
    def _extract_date(self, date_str: str) -> str:
        """استخراج السنة من تنسيقات التاريخ المختلفة"""
        if not date_str:
            return ''
        patterns = [
            r'(\d{4})',
            r'(\d{4})-\d{2}-\d{2}',
            r'\d{2}/(\d{4})',
            r'(\d{4})-\d{2}',
            r'(\d{4})\s*年',
            r'c?\.?\s*(\d{4})'
        ]
        for pattern in patterns:
            match = re.search(pattern, str(date_str))
            if match:
                return match.group(1)
        numbers = re.findall(r'\d{4}', str(date_str))
        if numbers:
            return numbers[0]
        return str(date_str)[:4] if len(str(date_str)) >= 4 else ''
    
    def _extract_isbn(self, identifiers: List[Dict], isbn_type: str) -> str:
        """استخراج ISBN محدد من قائمة المعرفات"""
        for identifier in identifiers:
            if identifier.get('type') == isbn_type:
                return identifier.get('identifier', '')
        return ''
    
    def _merge_results(self, results: List[Dict], isbn: str) -> Dict:
        """دمج النتائج من مصادر متعددة"""
        merged = {
            'title': '',
            'authors': [],
            'publisher': '',
            'published_date': '',
            'description': '',
            'page_count': '',
            'categories': [],
            'language': 'en',
            'isbn_10': '',
            'isbn_13': isbn if len(isbn) == 13 else '',
            'edition': '',  # ✅ حقل الطبعة
            'sources': len(results),
            'confidence': 'low'
        }
        
        high_confidence_sources = [r for r in results if r.get('confidence') == 'high']
        medium_confidence_sources = [r for r in results if r.get('confidence') == 'medium']
        sources_priority = high_confidence_sources + medium_confidence_sources
        
        for source in sources_priority:
            # العنوان
            if not merged['title'] and source.get('title'):
                merged['title'] = source['title']
            # المؤلفون
            if not merged['authors']:
                if source.get('authors'):
                    merged['authors'] = source['authors']
                elif source.get('author'):
                    merged['authors'] = [source['author']]
            # الناشر
            if not merged['publisher']:
                if source.get('publisher'):
                    merged['publisher'] = source['publisher']
                elif source.get('publishers'):
                    merged['publisher'] = ', '.join(source['publishers'])
            # تاريخ النشر
            if not merged['published_date'] and source.get('published_date'):
                merged['published_date'] = source['published_date']
            # الوصف
            if not merged['description']:
                if source.get('description'):
                    merged['description'] = source['description']
                elif source.get('synopsis'):
                    merged['description'] = source['synopsis']
            # عدد الصفحات
            if not merged['page_count']:
                if source.get('page_count'):
                    merged['page_count'] = source['page_count']
                elif source.get('pages'):
                    merged['page_count'] = source['pages']
                elif source.get('number_of_pages'):
                    merged['page_count'] = source['number_of_pages']
            # التصنيفات
            if not merged['categories']:
                if source.get('categories'):
                    merged['categories'] = source['categories']
                elif source.get('subjects'):
                    merged['categories'] = source['subjects']
            # ISBN
            if not merged['isbn_10'] and source.get('isbn_10'):
                merged['isbn_10'] = source['isbn_10']
            if not merged['isbn_13'] and source.get('isbn_13'):
                merged['isbn_13'] = source['isbn_13']
            # الطبعة (edition) – الأولوية للمصادر عالية الثقة
            if not merged['edition'] and source.get('edition'):
                merged['edition'] = source['edition']
        
        # حساب مستوى الثقة
        data_points = sum([
            1 if merged['title'] else 0,
            1 if merged['authors'] else 0,
            1 if merged['publisher'] else 0,
            1 if merged['published_date'] else 0,
            1 if merged['description'] else 0
        ])
        if data_points >= 4:
            merged['confidence'] = 'high'
        elif data_points >= 2:
            merged['confidence'] = 'medium'
        
        # التأكد من أن المؤلفين قائمة
        if not isinstance(merged['authors'], list):
            if merged['authors']:
                merged['authors'] = [merged['authors']]
            else:
                merged['authors'] = []
        
        return merged
    
    def _get_empty_metadata(self, isbn: str) -> Dict:
        """إرجاع بيانات وصفية فارغة"""
        return {
            'title': '',
            'authors': [],
            'publisher': '',
            'published_date': '',
            'description': '',
            'page_count': '',
            'categories': [],
            'language': 'en',
            'isbn_10': isbn if len(isbn) == 10 else '',
            'isbn_13': isbn if len(isbn) == 13 else '',
            'edition': '',
            'sources': 0,
            'confidence': 'low'
        }