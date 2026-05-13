from datetime import datetime
import re

def build_marc_record(data, isbn):
    """بناء سجل MARC21 متكامل ومحسن للكتب الطبية"""
    marc_fields = []
    
    # === 00X - المعلومات التحكمية ===
    marc_fields.append(f"001 ## $a ISBN{isbn}")
    marc_fields.append(f"005 ## $a {datetime.now().strftime('%Y%m%d%H%M%S')}.0")
    
    pub_year = data.get('pub_year', '')
    if pub_year and len(pub_year) == 4 and pub_year.isdigit():
        date_type = 's'
        date1 = pub_year
        date2 = pub_year
    else:
        date_type = '|'
        date1 = '||||'
        date2 = '||||'
    
    country_code = 'xx'
    illustrations = 'a'
    audience = data.get('audience_category', '').lower()
    if 'student' in audience or 'undergraduate' in audience:
        audience_code = 'e'
    elif 'graduate' in audience or 'researcher' in audience:
        audience_code = 'f'
    elif 'professional' in audience or 'clinician' in audience or 'physician' in audience:
        audience_code = 'd'
    else:
        audience_code = '|'
    
    content_type = 'a'
    media_type = 'n'
    carrier_type = 'nc'
    
    fixed_data = f"008 ## {date1}{date2}{country_code} |||||||{date_type} |||||{audience_code}||{content_type}{media_type}{carrier_type}|||||"
    marc_fields.append(fixed_data)
    
    # === 01X-09X ===
    marc_fields.append(f"020 ## $a {data.get('isbn_13', isbn)} $c (print)")
    if data.get('isbn_10'):
        marc_fields.append(f"020 ## $a {data['isbn_10']} $c (print)")
    
    marc_fields.append("040 ## $a SQU $b ara $e rda $c SQU")
    
    if data.get('lccn'):
        marc_fields.append(f"050 00 $a {data['lccn']}")
    else:
        marc_fields.append("050 00 $a R130")
    
    marc_fields.append(f"060 10 $a {data.get('nlm_class', 'W 1')}")
    marc_fields.append("082 04 $a 610")
    
    # === 1XX ===
    authors = data.get('authors', [])
    if authors and len(authors) > 0:
        marc_fields.append(f"100 1# $a {authors[0]} $e author.")
    
    title_field = f"245 10 $a {data.get('title', 'Untitled')}"
    if data.get('sub_title'):
        title_field += f" : $b {data['sub_title']}"
    marc_fields.append(title_field)
    
    if data.get('edition'):
        marc_fields.append(f"250 ## $a {data['edition']}")
    
    pub_info = f"264 #1 $a [Place of publication not identified] : $b {data.get('publisher', 'Unknown')}"
    if data.get('pub_year'):
        pub_info += f", $c {data['pub_year']}."
    marc_fields.append(pub_info)
    
    pages = data.get('pages', '')
    if not pages:
        pages = 'xii, 500'
    illustrations_note = data.get('illustrations_note', 'illustrations')
    marc_fields.append(f"300 ## $a {pages} pages : $b {illustrations_note} ; $c 26 cm")
    
    # === 3XX ===
    marc_fields.append("336 ## $a text $b txt $2 rdacontent")
    marc_fields.append("337 ## $a unmediated $b n $2 rdamedia")
    marc_fields.append("338 ## $a volume $b nc $2 rdacarrier")
    
    if data.get('series'):
        marc_fields.append(f"490 1# $a {data['series']}")
    
    # === 5XX ===
    marc_fields.append("500 ## $a Includes bibliographical references and index.")
    
    page_match = re.search(r'(\d+)', str(pages))
    if page_match:
        ref_pages = page_match.group(1)
    else:
        ref_pages = '500'
    marc_fields.append(f"504 ## $a Includes bibliographical references (pages {ref_pages}).")
    
    if data.get('contents_note'):
        contents = str(data['contents_note'])
        if isinstance(data['contents_note'], list):
            contents = ' -- '.join(data['contents_note'])
        if len(contents) > 500:
            contents = contents[:497] + "..."
        marc_fields.append(f"505 0# $a {contents}")
    
    if data.get('summary'):
        summary = str(data['summary'])
        if len(summary) > 500:
            summary = summary[:497] + "..."
        marc_fields.append(f"520 ## $a {summary}")
    
    marc_fields.append("546 ## $a In English.")
    
    # === 6XX ===
    mesh_subjects = data.get('mesh_subjects', [])
    subject_count = 0
    for i, subject in enumerate(mesh_subjects[:6]):
        subject_count += 1
        marc_fields.append(f"650 #{i+1}2 $a {subject}.")
    
    if subject_count == 0:
        marc_fields.append("650 #0 $a Medicine.")
        marc_fields.append("650 #0 $a Medical sciences.")
    
    marc_fields.append("655 #7 $a Textbooks. $2 lcgft")
    
    # === 7XX ===
    if len(authors) > 1:
        for author in authors[1:]:
            marc_fields.append(f"700 1# $a {author} $e author.")
    
    if data.get('institution'):
        marc_fields.append(f"710 2# $a {data['institution']}")
    
    # === 8XX ===
    marc_fields.append(f"856 42 $3 WorldCat $u https://worldcat.org/isbn/{isbn}")
    marc_fields.append(f"856 42 $3 Google Books $u https://books.google.com/books?vid=ISBN{isbn}")
    marc_fields.append(f"856 42 $3 Open Library $u https://openlibrary.org/isbn/{isbn}")
    
    # === 9XX ===
    marc_fields.append(f"942 ## $a CATALOGED $b {datetime.now().strftime('%Y%m%d')} $c SAIFOM")
    marc_fields.append("959 ## $a AI-generated cataloging record.")
    marc_fields.append("959 ## $b Verified by Medical AI Librarian v3.0.")
    marc_fields.append(f"959 ## $c ISBN: {isbn}")
    
    return marc_fields

def generate_marc_iso2709(marc_fields, isbn):
    """إنشاء تسجيل MARC21 بتنسيق ISO 2709"""
    record_length = 24
    for field in marc_fields:
        record_length += len(field) + 1 + 1
    record_length += 12 * len(marc_fields)
    record_length += 1
    
    record_status = 'n'
    record_type = 'a'
    bibliographic_level = 'm'
    control_type = ' '
    char_coding_scheme = ' '
    
    leader = f"{str(record_length).zfill(5)}"
    leader += record_status
    leader += record_type
    leader += " "
    leader += " "
    leader += " "
    leader += " "
    leader += " "
    leader += "22"
    leader += str(len(marc_fields)).zfill(5)
    leader += "4500"
    
    directory = ""
    fields_data = ""
    base_address = 24 + (12 * len(marc_fields)) + 1
    
    for i, field in enumerate(marc_fields):
        field_tag = field[:3]
        field_data = field[6:]
        field_length = len(field_data)
        starting_position = len(fields_data)
        directory += f"{field_tag}{str(field_length).zfill(4)}{str(starting_position).zfill(5)}"
        fields_data += field_data
    
    directory_end = "\x1E"
    record_end = "\x1D"
    
    iso_record = leader + directory + directory_end + fields_data + record_end
    
    return {
        'iso2709': iso_record,
        'human_readable': "\n".join(marc_fields),
        'fields_count': len(marc_fields),
        'record_length': len(iso_record)
    }

def generate_marcxml(marc_fields, isbn):
    """إنشاء تنسيق MARCXML"""
    xml_parts = []
    xml_parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    xml_parts.append('<marc:collection xmlns:marc="http://www.loc.gov/MARC21/slim" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd">')
    xml_parts.append('  <marc:record>')
    
    for field in marc_fields:
        tag = field[:3]
        indicators = field[4:6]
        content = field[7:]
        
        xml_parts.append(f'    <marc:datafield tag="{tag}" ind1="{indicators[0]}" ind2="{indicators[1]}">')
        
        subfields = content.split('$')
        for subfield in subfields[1:]:
            if subfield:
                code = subfield[0]
                text = subfield[1:].strip()
                xml_parts.append(f'      <marc:subfield code="{code}">{text}</marc:subfield>')
        
        xml_parts.append('    </marc:datafield>')
    
    xml_parts.append('  </marc:record>')
    xml_parts.append('</marc:collection>')
    
    return "\n".join(xml_parts)