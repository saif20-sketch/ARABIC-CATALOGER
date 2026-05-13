NLM_FULL_CLASSIFICATION = {
    "W": {"name": "Health Professions", "description": "General works on medicine and health",
         "subcategories": {
             "W 1": {"name": "Reference Works", "description": "Medical encyclopedias, dictionaries, directories"},
             "W 13": {"name": "Dictionaries", "description": "Medical dictionaries and terminology"},
             "W 15": {"name": "Nomenclature", "description": "Classification systems and nomenclature"},
             "W 18": {"name": "Medical Education", "description": "Textbooks, teaching materials, curriculum"},
             "W 20": {"name": "Research", "description": "Medical research methodology"},
             "W 20.5": {"name": "Research Methodology", "description": "Study design, statistics in medicine"},
             "W 21": {"name": "Computer Applications", "description": "Medical informatics, computer applications"},
             "W 26": {"name": "Medical Writing", "description": "Scientific writing, medical journalism"},
             "W 50": {"name": "Ethics", "description": "Medical ethics, bioethics"},
             "W 62": {"name": "Forensic Medicine", "description": "Legal medicine, medical jurisprudence"},
             "W 74": {"name": "Medical Economics", "description": "Health economics, medical finance"},
             "W 76": {"name": "Practice Management", "description": "Medical practice administration"},
             "W 84": {"name": "Health Facilities", "description": "Hospitals, clinics, health centers"},
             "W 85": {"name": "Medical Personnel", "description": "Physicians, nurses, allied health personnel"},
             "W 87": {"name": "Medical Societies", "description": "Professional organizations"},
             "W 89": {"name": "Family Practice", "description": "General practice, primary care"}
         }},
    "WA": {"name": "Public Health", "description": "Public health, preventive medicine",
          "subcategories": {
              "WA 1": {"name": "Reference Works", "description": "Public health reference materials"},
              "WA 100": {"name": "Epidemiology", "description": "Disease distribution and determinants"},
              "WA 105": {"name": "Statistics", "description": "Vital statistics, health statistics"},
              "WA 200": {"name": "Environmental Health", "description": "Environmental factors affecting health"},
              "WA 250": {"name": "Occupational Health", "description": "Workplace health and safety"},
              "WA 300": {"name": "Disease Prevention", "description": "Preventive medicine, vaccination"},
              "WA 390": {"name": "Nutrition", "description": "Nutrition and public health"},
              "WA 395": {"name": "Health Promotion", "description": "Health education, wellness promotion"},
              "WA 400": {"name": "Health Services", "description": "Health care delivery systems"},
              "WA 525": {"name": "Maternal Health", "description": "Maternal and child health services"},
              "WA 590": {"name": "Mental Health", "description": "Community mental health services"}
          }},
    # يمكنك إضافة المزيد من التصنيفات هنا إذا أردت
}

def get_nlm_category(code: str) -> dict:
    main_category = code.split()[0] if ' ' in code else code
    subcategory = code.split()[1] if ' ' in code else None
    
    if main_category in NLM_FULL_CLASSIFICATION:
        category_info = NLM_FULL_CLASSIFICATION[main_category]
        if subcategory and subcategory in category_info.get('subcategories', {}):
            return {
                'main_category': main_category,
                'main_name': category_info['name'],
                'main_description': category_info['description'],
                'subcategory': subcategory,
                'subcategory_name': category_info['subcategories'][subcategory]['name'],
                'subcategory_description': category_info['subcategories'][subcategory]['description']
            }
        return {
            'main_category': main_category,
            'main_name': category_info['name'],
            'main_description': category_info['description']
        }
    return {'error': 'Classification not found'}

def search_nlm_by_keyword(keyword: str) -> list:
    results = []
    keyword_lower = keyword.lower()
    for main_code, main_info in NLM_FULL_CLASSIFICATION.items():
        main_name = main_info['name'].lower()
        main_desc = main_info['description'].lower()
        if (keyword_lower in main_name or keyword_lower in main_desc or keyword_lower in main_code.lower()):
            results.append({
                'code': main_code,
                'name': main_info['name'],
                'description': main_info['description'],
                'type': 'main_category'
            })
        for sub_code, sub_info in main_info.get('subcategories', {}).items():
            full_code = f"{main_code} {sub_code}" if sub_code != '1' else main_code
            sub_name = sub_info['name'].lower()
            sub_desc = sub_info['description'].lower()
            if (keyword_lower in sub_name or keyword_lower in sub_desc or keyword_lower in full_code.lower()):
                results.append({
                    'code': full_code,
                    'name': sub_info['name'],
                    'description': sub_info['description'],
                    'type': 'subcategory'
                })
    return results[:20]

def validate_nlm_code(code: str) -> dict:
    result = get_nlm_category(code)
    if 'error' not in result:
        return {
            'valid': True,
            'code': code,
            'details': result
        }
    suggestions = search_nlm_by_keyword(code.split()[0] if ' ' in code else code)
    return {
        'valid': False,
        'code': code,
        'suggestions': suggestions[:5]
    }