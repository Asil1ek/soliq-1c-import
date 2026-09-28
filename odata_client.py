"""
1C OData Client — Optimized
- Nomenklaturani bir so'rovda yuklab cache qiladi
- Faqat yangi tovarlarni alohida yaratadi
- Document yaratish bitta so'rov (tabular qism ichida)
"""
import http.client
import json
import base64
from datetime import datetime, date

import os

# ─── SOZLAMALAR ────────────────────────────────────────────────────────────────
ODATA_HOST  = 'clobus.uz'
ODATA_BASE  = '/a/acc317/76590/odata/standard.odata'
# XAVFSIZLIK: Parollar GitHub'da ko'rinib qolmasligi uchun Render panelidan (Environment Variables) kiritiladi.
ODATA_LOGIN = os.environ.get('ODATA_LOGIN', '') 
ODATA_PASS  = os.environ.get('ODATA_PASS', '')
SKLAD_KEY   = '2f67558e-b741-11f1-992a-e8ebd3d273f6'  # "Sklad"



NULL_KEY = '00000000-0000-0000-0000-000000000000'

# URL-encoded entity nomlari
_E_REALIZ   = 'Document_%D0%A0%D0%B5%D0%B0%D0%BB%D0%B8%D0%B7%D0%B0%D1%86%D0%B8%D1%8F%D0%A2%D0%BE%D0%B2%D0%B0%D1%80%D0%BE%D0%B2%D0%A3%D1%81%D0%BB%D1%83%D0%B3'
_E_VOZVRAT  = 'Document_%D0%92%D0%BE%D0%B7%D0%B2%D1%80%D0%B0%D1%82%D0%A2%D0%BE%D0%B2%D0%B0%D1%80%D0%BE%D0%B2%D0%9E%D1%82%D0%9F%D0%BE%D0%BA%D1%83%D0%BF%D0%B0%D1%82%D0%B5%D0%BB%D1%8F'
_E_NOMENKL  = 'Catalog_%D0%9D%D0%BE%D0%BC%D0%B5%D0%BD%D0%BA%D0%BB%D0%B0%D1%82%D1%83%D1%80%D0%B0'
_E_KONTRG   = 'Catalog_%D0%9A%D0%BE%D0%BD%D1%82%D1%80%D0%B0%D0%B3%D0%B5%D0%BD%D1%82%D1%8B'

# ─── IN-MEMORY CACHE ───────────────────────────────────────────────────────────
_cache_loaded    = False
_cache_by_name   = {}   # lower(Description) → Ref_Key
_cache_by_code   = {}   # Код → Ref_Key
_cache_by_barcode= {}   # Артикул → Ref_Key
_kontragent_key  = None

# ─── HTTP YORDAMCHI ────────────────────────────────────────────────────────────
def _creds():
    return base64.b64encode(f'{ODATA_LOGIN}:{ODATA_PASS}'.encode()).decode()

def _request(method: str, path: str, body=None, timeout=30):
    headers = {
        'Authorization': f'Basic {_creds()}',
        'Accept': 'application/json',
        'Content-Type': 'application/json; charset=utf-8',
        'Prefer': 'return=representation'
    }
    conn = http.client.HTTPSConnection(ODATA_HOST, timeout=timeout)
    body_bytes = json.dumps(body, ensure_ascii=False).encode('utf-8') if body else None
    conn.request(method, path, body=body_bytes, headers=headers)
    resp = conn.getresponse()
    data = resp.read().decode('utf-8')
    conn.close()
    if resp.status in (200, 201):
        try:
            return True, json.loads(data)
        except Exception:
            return True, {}
    else:
        return False, {'status': resp.status, 'body': data[:800]}

def _get_page(entity: str, skip: int = 0, top: int = 1000, select: str = '') -> list:
    sel = f'&$select={select}' if select else ''
    path = f'{ODATA_BASE}/{entity}?$format=json&$top={top}&$skip={skip}{sel}'
    ok, data = _request('GET', path, timeout=30)
    if ok:
        return data.get('value', [])
    return []

def _post(entity: str, body: dict, timeout: int = 180):
    path = f'{ODATA_BASE}/{entity}?$format=json'
    return _request('POST', path, body, timeout=timeout)


# ─── CACHE YUKLASH (bir marta, butun nomenklaturani) ──────────────────────────
def _load_nomenkl_cache():
    """1C dagi barcha nomenklaturani bir marta yuklab olib cachega saqlaydi."""
    global _cache_loaded, _cache_by_name, _cache_by_code, _cache_by_barcode
    if _cache_loaded:
        return

    print('[OData] Nomenklatura cache yuklanmoqda...')
    skip = 0
    total = 0
    while True:
        rows = _get_page(
            _E_NOMENKL, skip=skip, top=1000,
            select='Ref_Key%2CDescription%2C%D0%9A%D0%BE%D0%B4%2C%D0%90%D1%80%D1%82%D0%B8%D0%BA%D1%83%D0%BB'
        )
        if not rows:
            break
        for r in rows:
            key  = r.get('Ref_Key', '')
            name = r.get('Description', '').lower().strip()
            code = str(r.get('Код', '') or '').strip()
            art  = str(r.get('Артикул', '') or '').strip()
            if name: _cache_by_name[name]    = key
            if code: _cache_by_code[code]    = key
            if art:  _cache_by_barcode[art]  = key
        total += len(rows)
        if len(rows) < 1000:
            break
        skip += 1000

    _cache_loaded = True
    print(f'[OData] Cache yuklandi: {total} ta nomenklatura')

# ─── NOMENKLATURA TOPISH / YARATISH ───────────────────────────────────────────
def _get_or_create_nomenkl(tovar_nomi: str, kod: str, barcode: str, ikpu: str) -> str:
    """Cache dan topadi, topilmasa 1C da yangi yaratadi."""
    _load_nomenkl_cache()

    name_key = tovar_nomi.lower().strip()
    kod_s    = str(kod or '').strip()
    bc_s     = str(barcode or '').strip()

    # Cache dan qidirish
    if kod_s   and kod_s   in _cache_by_code:    return _cache_by_code[kod_s]
    if bc_s    and bc_s    in _cache_by_barcode:  return _cache_by_barcode[bc_s]
    if name_key and name_key in _cache_by_name:   return _cache_by_name[name_key]

    # 1C da yangi yaratish
    new_item = {
        'Description': tovar_nomi[:150],
        'Код'        : kod_s[:9]  if kod_s else '',
        'Артикул'    : bc_s[:25]  if bc_s  else '',
        'СтавкаНДС'  : 'НДС12',
        'ТипНоменклатуры': 'Товар',
    }
    ok, result = _post(_E_NOMENKL, new_item)
    if ok and result.get('Ref_Key'):
        key = result['Ref_Key']
        # Cachega qo'shish
        if name_key: _cache_by_name[name_key]   = key
        if kod_s:    _cache_by_code[kod_s]       = key
        if bc_s:     _cache_by_barcode[bc_s]     = key
        return key

    return NULL_KEY

# ─── KONTRAGENT ────────────────────────────────────────────────────────────────
def _get_or_create_kontragent() -> str:
    global _kontragent_key
    if _kontragent_key:
        return _kontragent_key

    # Avval oldin yaratilganini qidirish (Ref_Key ni bilamiz)
    known_key = 'b8c604c5-b741-11f1-992a-e8ebd3d273f6'
    ok, data = _request('GET', f'{ODATA_BASE}/{_E_KONTRG}(guid\'{known_key}\')?$format=json')
    if ok and data.get('Ref_Key'):
        _kontragent_key = data['Ref_Key']
        return _kontragent_key

    # Yaratish
    body = {
        'Description'      : 'Chakana xaridor',
        'ЮрФизЛицо'        : 'ФизическоеЛицо',
        'НаименованиеПолное': 'Chakana xaridor (Soliq cheklar)',
    }
    ok, result = _post(_E_KONTRG, body)
    if ok and result.get('Ref_Key'):
        _kontragent_key = result['Ref_Key']
        return _kontragent_key

    return NULL_KEY

# ─── HUJJAT YARATISH (bitta so'rov) ───────────────────────────────────────────
def _build_items(items: list) -> tuple:
    """
    items ro'yxatidan 1C Товары jadvalini tuzadi.
    Barcha nomenklaturalarni cache orqali topadi/yaratadi.
    Returns: (tovary_list, total_sum, total_nds)
    """
    tovary = []
    total_sum = 0.0
    total_nds = 0.0

    for idx, item in enumerate(items, start=1):
        nom_key = _get_or_create_nomenkl(
            item.get('TovarNomi', 'Tovar'),
            item.get('Kod', ''),
            item.get('Barcode', ''),
            item.get('IKPU', '')
        )
        summa  = float(item.get('Summa',   0) or 0)
        miqdor = float(item.get('Miqdori', 0) or 0)
        narx   = float(item.get('Narxi',   0) or 0)
        qqs    = float(item.get('QQS',     0) or 0)

        if miqdor <= 0:
            continue

        total_sum += summa
        total_nds += qqs

        tovary.append({
            'LineNumber'       : idx,
            'Номенклатура_Key' : nom_key,
            'Количество'       : round(miqdor, 3),
            'Цена'             : round(narx, 2),
            'Сумма'            : round(summa, 2),
            'СуммаНДС'         : round(qqs, 2),
            'СтавкаНДС'        : 'НДС12',
            'Склад_Key'        : SKLAD_KEY,
        })

    return tovary, round(total_sum, 2), round(total_nds, 2)

# ─── SOTUV HUJJATI ─────────────────────────────────────────────────────────────
def create_realization(doc_date: date, items: list, doc_number: str = '') -> dict:
    """
    1C da Реализация товаров и услуг yaratadi.
    items: [{'TovarNomi','Kod','Barcode','IKPU','Miqdori','Narxi','Summa','QQS'}, ...]
    """
    try:
        kontragent_key = _get_or_create_kontragent()
        date_str = datetime.combine(doc_date, datetime.min.time()).strftime('%Y-%m-%dT%H:%M:%S')

        print(f'[OData] Nomenklatura tayyorlanmoqda ({len(items)} ta tovar)...')
        tovary, total_sum, total_nds = _build_items(items)
        print(f'[OData] {len(tovary)} ta tovar tayyor. Hujjat yuborilmoqda...')

        doc_body = {
            'Date'           : date_str,
            'Number'         : doc_number or f'SOLIQ-{doc_date.strftime("%d%m%Y")}',
            'Контрагент_Key' : kontragent_key,
            'Склад_Key'      : SKLAD_KEY,
            'СуммаДокумента' : total_sum,
            'Posted'         : False,
            'Товары'         : tovary,
        }

        ok, result = _post(_E_REALIZ, doc_body)
        if ok:
            print(f'[OData] Sotuv hujjati yaratildi: {result.get("Number", "")}')
            return {
                'success' : True,
                'ref_key' : result.get('Ref_Key', ''),
                'number'  : result.get('Number', '').strip(),
                'doc_date': date_str,
                'items_count': len(tovary),
            }
        else:
            return {'success': False, 'error': result.get('body', str(result))}

    except Exception as e:
        import traceback
        return {'success': False, 'error': str(e) + '\n' + traceback.format_exc()}

# ─── QAYTARISH HUJJATI ─────────────────────────────────────────────────────────
def create_return(doc_date: date, items: list, doc_number: str = '') -> dict:
    """
    1C da Возврат товаров от покупателя yaratadi.
    """
    try:
        kontragent_key = _get_or_create_kontragent()
        date_str = datetime.combine(doc_date, datetime.min.time()).strftime('%Y-%m-%dT%H:%M:%S')

        print(f'[OData] Qaytarish nomenklatura tayyorlanmoqda ({len(items)} ta tovar)...')
        tovary, total_sum, total_nds = _build_items(items)
        print(f'[OData] {len(tovary)} ta tovar tayyor. Qaytarish hujjati yuborilmoqda...')

        doc_body = {
            'Date'           : date_str,
            'Number'         : doc_number or f'VOZVRAT-{doc_date.strftime("%d%m%Y")}',
            'Контрагент_Key' : kontragent_key,
            'Склад_Key'      : SKLAD_KEY,
            'СуммаДокумента' : total_sum,
            'Posted'         : False,
            'Товары'         : tovary,
        }

        ok, result = _post(_E_VOZVRAT, doc_body)
        if ok:
            print(f'[OData] Qaytarish hujjati yaratildi: {result.get("Number", "")}')
            return {
                'success' : True,
                'ref_key' : result.get('Ref_Key', ''),
                'number'  : result.get('Number', '').strip(),
                'doc_date': date_str,
                'items_count': len(tovary),
            }
        else:
            return {'success': False, 'error': result.get('body', str(result))}

    except Exception as e:
        import traceback
        return {'success': False, 'error': str(e) + '\n' + traceback.format_exc()}

# ─── CACHE TOZALASH (yangi run uchun) ─────────────────────────────────────────
def reset_cache():
    global _cache_loaded, _cache_by_name, _cache_by_code, _cache_by_barcode, _kontragent_key
    _cache_loaded    = False
    _cache_by_name   = {}
    _cache_by_code   = {}
    _cache_by_barcode= {}
    _kontragent_key  = None
