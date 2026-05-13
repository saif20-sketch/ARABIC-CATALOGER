import requests
import os
import urllib.parse
from typing import Dict, Optional

class EnhancedCoverFetcher:
    """مسترد محسن لأغلفة الكتب من مصادر متعددة مع دعم HTTPS والفحص الذكي"""
    
    def __init__(self):
        self.sources = [
            self._try_google_books,
            self._try_openlibrary,
            self._try_librarything,
            self._try_amazon,
            self._try_bookdepository,
            self._try_barnes_noble,
            self._try_via_placeholder,  # ✅ مصدر احتياطي إضافي
            self._try_fakeimg          # ✅ مصدر احتياطي إضافي
        ]
    
    def get_cover(self, isbn: str, title: Optional[str] = None) -> Dict:
        """الحصول على غلاف الكتاب من أفضل مصدر متاح"""
        for source_func in self.sources:
            try:
                result = source_func(isbn)
                if result and result.get('url') and self._is_image_accessible(result['url']):
                    return result
            except Exception as e:
                continue
        return self._generate_smart_placeholder(isbn, title)
    
    def _is_image_accessible(self, url: str) -> bool:
        """التحقق من أن الصورة قابلة للعرض (تستخدم GET بدلاً من HEAD)"""
        try:
            response = requests.get(url, timeout=5, stream=True)
            content_type = response.headers.get('Content-Type', '')
            return response.status_code == 200 and content_type.startswith('image/')
        except:
            return False
    
    def _try_google_books(self, isbn: str) -> Optional[Dict]:
        try:
            url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and len(data['items']) > 0:
                    volume_info = data['items'][0]['volumeInfo']
                    image_links = volume_info.get('imageLinks', {})
                    cover_url = None
                    # الأولوية للصور الأكبر
                    for size in ['extraLarge', 'large', 'medium', 'small', 'thumbnail']:
                        if image_links.get(size):
                            cover_url = image_links[size]
                            break
                    if cover_url:
                        # تحويل HTTP إلى HTTPS
                        cover_url = cover_url.replace('http://', 'https://')
                        return {
                            'url': cover_url,
                            'source': 'Google Books',
                            'status': 'success',
                            'quality': 'high'
                        }
        except:
            pass
        return None
    
    def _try_openlibrary(self, isbn: str) -> Optional[Dict]:
        try:
            cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
            if self._is_image_accessible(cover_url):
                return {
                    'url': cover_url,
                    'source': 'OpenLibrary',
                    'status': 'success',
                    'quality': 'medium'
                }
        except:
            pass
        return None
    
    def _try_librarything(self, isbn: str) -> Optional[Dict]:
        api_key = os.getenv('LIBRARYTHING_KEY')
        if not api_key:
            return None
        try:
            cover_url = f"https://covers.librarything.com/devkey/{api_key}/large/isbn/{isbn}"
            if self._is_image_accessible(cover_url):
                return {
                    'url': cover_url,
                    'source': 'LibraryThing',
                    'status': 'success',
                    'quality': 'medium'
                }
        except:
            pass
        return None
    
    def _try_amazon(self, isbn: str) -> Optional[Dict]:
        try:
            # Amazon يفضل ISBN-10
            isbn_clean = isbn.replace('-', '')
            cover_url = f"https://images-na.ssl-images-amazon.com/images/P/{isbn_clean}.01.LZZZZZZZ.jpg"
            if self._is_image_accessible(cover_url):
                return {
                    'url': cover_url,
                    'source': 'Amazon',
                    'status': 'success',
                    'quality': 'high'
                }
        except:
            pass
        return None
    
    def _try_bookdepository(self, isbn: str) -> Optional[Dict]:
        try:
            cover_url = f"https://d1w7fb2mkkr3kw.cloudfront.net/assets/images/book/lrg/{isbn[:3]}/{isbn}.jpg"
            if self._is_image_accessible(cover_url):
                return {
                    'url': cover_url,
                    'source': 'Book Depository',
                    'status': 'success',
                    'quality': 'medium'
                }
        except:
            pass
        return None
    
    def _try_barnes_noble(self, isbn: str) -> Optional[Dict]:
        try:
            # استخدام HTTPS
            cover_url = f"https://images.barnesandnoble.com/pImages/{isbn}.jpg"
            if self._is_image_accessible(cover_url):
                return {
                    'url': cover_url,
                    'source': 'Barnes & Noble',
                    'status': 'success',
                    'quality': 'medium'
                }
        except:
            pass
        return None
    
    def _try_via_placeholder(self, isbn: str) -> Optional[Dict]:
        """مصدر احتياطي - via.placeholder.com (خدمة صور افتراضية)"""
        try:
            cover_url = f"https://via.placeholder.com/400x600.png?text=ISBN%3A{isbn}"
            return {
                'url': cover_url,
                'source': 'via.placeholder.com',
                'status': 'fallback',
                'quality': 'low'
            }
        except:
            return None
    
    def _try_fakeimg(self, isbn: str) -> Optional[Dict]:
        """مصدر احتياطي آخر - fakeimg.pl"""
        try:
            cover_url = f"https://fakeimg.pl/400x600/cccccc/666?text=ISBN%3A{isbn}"
            return {
                'url': cover_url,
                'source': 'fakeimg.pl',
                'status': 'fallback',
                'quality': 'low'
            }
        except:
            return None
    
    def _generate_smart_placeholder(self, isbn: str, title: Optional[str] = None) -> Dict:
        """إنشاء placeholder ذكي باستخدام Data URI (يعمل حتى بدون إنترنت)"""
        # ألوان مختلفة لأنواع الكتب
        color_schemes = {
            'medical': ('#e3f2fd', '#1565c0', '🏥'),
            'science': ('#f3e5f5', '#7b1fa2', '🔬'),
            'textbook': ('#fff3e0', '#ef6c00', '📚'),
            'default': ('#f5f5f5', '#424242', '📖')
        }
        
        book_type = 'default'
        if title:
            title_lower = title.lower()
            if any(word in title_lower for word in ['medical', 'medicine', 'clinic', 'hospital', 'surgery']):
                book_type = 'medical'
            elif any(word in title_lower for word in ['science', 'biology', 'chemistry', 'physics', 'anatomy']):
                book_type = 'science'
            elif any(word in title_lower for word in ['textbook', 'guide', 'manual', 'handbook', 'student']):
                book_type = 'textbook'
        
        bg_color, text_color, icon = color_schemes[book_type]
        
        # إنشاء نص العرض
        display_text = f"ISBN: {isbn}"
        if title:
            short_title = title[:25] + ('...' if len(title) > 25 else '')
            display_text = f"{icon} {short_title}\nISBN: {isbn}"
        
        # محاولة استخدام placehold.co أولاً
        try:
            encoded_text = urllib.parse.quote(display_text)
            placeholder_url = f"https://placehold.co/400x600/{bg_color.strip('#')}/{text_color.strip('#')}?text={encoded_text}&font=roboto"
            # تحقق من أن الخدمة تعمل
            if self._is_image_accessible(placeholder_url):
                return {
                    'url': placeholder_url,
                    'source': 'Smart Placeholder (placehold.co)',
                    'status': 'fallback',
                    'quality': 'low',
                    'type': book_type
                }
        except:
            pass
        
        # إذا فشل placehold.co، استخدم fakeimg.pl
        try:
            fakeimg_url = f"https://fakeimg.pl/400x600/{bg_color.strip('#')}/{text_color.strip('#')}?text={urllib.parse.quote(display_text)}"
            return {
                'url': fakeimg_url,
                'source': 'Smart Placeholder (fakeimg.pl)',
                'status': 'fallback',
                'quality': 'low',
                'type': book_type
            }
        except:
            pass
        
        # الحل الأخير: Data URI (صورة SVG داخلية، تعمل بدون إنترنت)
        svg = f'''<svg width="400" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect width="400" height="600" fill="{bg_color}"/>
            <text x="200" y="200" font-size="20" text-anchor="middle" fill="{text_color}" font-family="Arial, sans-serif">
                {icon} {title if title else 'Book'}
            </text>
            <text x="200" y="300" font-size="16" text-anchor="middle" fill="{text_color}" font-family="Arial, sans-serif">
                ISBN: {isbn}
            </text>
        </svg>'''
        import base64
        svg_base64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
        data_uri = f"data:image/svg+xml;base64,{svg_base64}"
        
        return {
            'url': data_uri,
            'source': 'Data URI (local)',
            'status': 'fallback',
            'quality': 'low',
            'type': book_type
        }
    
    def get_all_covers(self, isbn: str) -> Dict:
        """الحصول على جميع الأغلفة المتاحة"""
        all_covers = []
        for source_func in self.sources:
            try:
                result = source_func(isbn)
                if result and result.get('url'):
                    all_covers.append(result)
            except:
                continue
        if not all_covers:
            placeholder = self._generate_smart_placeholder(isbn)
            all_covers.append(placeholder)
        return {
            'total': len(all_covers),
            'covers': all_covers,
            'best': all_covers[0] if all_covers else None
        }