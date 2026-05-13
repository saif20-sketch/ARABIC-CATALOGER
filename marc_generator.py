def build_rda_marc_record(data):
    marc = []
    # 020 - ISBN
    marc.append(f"020 ## $a {data['isbn']}")
    
    # 040 - مصدر الفهرسة (نظامك)
    marc.append(f"040 ## $a AR-智能 $b ara $e rda")
    
    # 050 - تصنيف مكتبة الكونجرس
    marc.append(f"050 00 $a {data['lcc_suggested']}")
    
    # 100 - المدخل الرئيسي للمؤلف
    marc.append(f"100 1# $a {data['author_primary']}, $e author.")
    
    # 245 - العنوان (RDA لا يختصر العنوان)
    marc.append(f"245 10 $a {data['title_statement']}")
    
    # 264 - بيانات النشر (RDA Standard)
    pub = data['publication']
    marc.append(f"264 #1 $a {pub['place']} : $b {pub['publisher']}, $c {pub['year']}.")
    
    # 300 - الوصف المادي
    illus = "illustrations" if data['physical_desc']['illus'] else ""
    marc.append(f"300 ## $a {data['physical_desc']['pages']} pages : $b {illus} ; $c 24 cm.")
    
    # 336, 337, 338 - حقول RDA الخاصة بنوع المحتوى والوسائط
    marc.append("336 ## $a text $b txt $2 rdacontent")
    marc.append("337 ## $a unmediated $b n $2 rdamedia")
    marc.append("338 ## $a volume $b nc $2 rdacarrier")
    
    # 650 - رؤوس الموضوعات (LCSH)
    for subject in data['subjects']:
        marc.append(f"650 #4 $a {subject}.")
        
    return marc

def generate_marc_iso2709(marc_fields):
    # تحويل الحقول إلى تنسيق ثنائي UTF-8 (ISO 2709)
    human_readable = "\n".join(marc_fields)
    return human_readable.encode('utf-8')
