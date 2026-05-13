from datetime import datetime

def build_marc_record(data, isbn):
    marc_fields = []
    
    # 001 - الرقم الموحد (ISBN)
    clean_isbn = str(isbn).replace('-', '')
    marc_fields.append(f"001 ## $a {clean_isbn}")
    
    # 100 - المؤلف الرئيسي
    author = data.get('authors', [''])[0] if data.get('authors') else "مؤلف غير معروف"
    marc_fields.append(f"100 1# $a {author}")
    
    # 245 - العنوان وذكر المسؤولية
    title = data.get('title', '')
    marc_fields.append(f"245 10 $a {title} $c {', '.join(data.get('authors', []))}")
    
    # 260 - بيانات النشر (محسن للعربية)
    location = data.get('pub_location', 'د.م')
    publisher = data.get('publisher', 'د.ن')
    year = data.get('pub_year', 'د.ت')
    marc_fields.append(f"260 ## $a {location} $b {publisher} $c {year}")
    
    # 520 - المستخلص (من الصور)
    if data.get('description'):
        marc_fields.append(f"520 ## $a {data['description']}")
        
    return marc_fields

def generate_marc_iso2709(marc_fields, isbn):
    # كود التحويل إلى ISO2709 (نفس منطقك السابق مع التأكد من UTF-8)
    human_readable = "\n".join(marc_fields)
    # (هنا يتم وضع منطق توليد Leader و Directory المبسط)
    return {
        'iso2709': human_readable.encode('utf-8'), 
        'human_readable': human_readable
    }
