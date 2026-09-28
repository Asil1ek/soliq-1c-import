import os
import io
import glob
import threading
import uuid as _uuid
from flask import Flask, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from processor import (
    process_soliq_file,
    export_to_1c_excel,
    load_nomenklatura_mapping,
    subtract_returns_from_sales
)
from odata_client import create_realization, create_return, reset_cache

# Background job storage: job_id → {status, result, error}
JOBS = {}


app = Flask(__name__, static_folder='static')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

CURRENT_DATA = {
    'sotuv_summary': None,
    'sotuv_grp': None,
    'sotuv_net': None,    # sotuv - qaytarish (net)
    'sotuv_raw': None,
    'qayt_summary': None,
    'qayt_grp': None,
    'qayt_raw': None,
}

def find_input_files(pattern_keyword):
    all_files = glob.glob(os.path.join(BASE_DIR, '*.xlsx')) + glob.glob(os.path.join(BASE_DIR, '*.xls'))
    matched = []
    for f in all_files:
        name = os.path.basename(f)
        if name.startswith('1C_') or name.startswith('Tayyor_') or 'output' in f.lower():
            continue
        if pattern_keyword.lower() in name.lower():
            matched.append(f)
    return matched

def find_all_nomenklatura_files():
    """Find all nomenklatura files (Kod Nomekulatura.xlsx, Kod Nomekulatura Davomi.xlsx, etc.)"""
    keywords = ['nomenklatura', 'nomekulatura', 'spravochnik', 'kod nomekulatura', 'kod nomenklatura']
    all_files = glob.glob(os.path.join(BASE_DIR, '*.xlsx')) + glob.glob(os.path.join(BASE_DIR, '*.xls'))
    matched = []
    seen = set()
    for f in all_files:
        name = os.path.basename(f).lower()
        if name.startswith('1c_') or name.startswith('tayyor_') or 'output' in f.lower():
            continue
        for kw in keywords:
            if kw in name and f not in seen:
                matched.append(f)
                seen.add(f)
                break
    return matched

STATIC_DIR = os.path.join(BASE_DIR, 'static')

@app.route('/')
def index():
    # 1. Try static/index.html
    p1 = os.path.join(STATIC_DIR, 'index.html')
    if os.path.exists(p1):
        return send_from_directory(STATIC_DIR, 'index.html')
    # 2. Try index.html in root directory (if user uploaded directly)
    p2 = os.path.join(BASE_DIR, 'index.html')
    if os.path.exists(p2):
        return send_from_directory(BASE_DIR, 'index.html')
    return f"index.html topilmadi! BASE_DIR: {BASE_DIR}, files: {os.listdir(BASE_DIR)}", 404

@app.route('/<path:filename>')
def serve_static(filename):
    # 1. Check in static/
    p1 = os.path.join(STATIC_DIR, filename)
    if os.path.exists(p1) and os.path.isfile(p1):
        return send_from_directory(STATIC_DIR, filename)
    # 2. Check in root
    p2 = os.path.join(BASE_DIR, filename)
    if os.path.exists(p2) and os.path.isfile(p2):
        return send_from_directory(BASE_DIR, filename)
    # Fallback to index
    return index()



@app.route('/api/status')
def status():
    sotuv_files = find_input_files('sotuv')
    qayt_files = find_input_files('qaytarish')
    nom_files = find_all_nomenklatura_files()

    return jsonify({
        'status': 'ready',
        'detected_files': {
            'sotuv': [os.path.basename(f) for f in sotuv_files],
            'qaytarish': [os.path.basename(f) for f in qayt_files],
            'nomenklatura': [os.path.basename(f) for f in nom_files]
        },
        'has_data': CURRENT_DATA['sotuv_summary'] is not None
    })

@app.route('/api/process', methods=['POST'])
def process():
    global CURRENT_DATA
    try:
        sotuv_file = request.files.get('sotuv_file')
        qayt_file = request.files.get('qayt_file')
        nom_file = request.files.get('nom_file')

        sotuv_path = None
        qayt_path = None
        nom_paths = []

        # Sotuv file
        if sotuv_file and sotuv_file.filename:
            sotuv_path = os.path.join(OUTPUT_DIR, secure_filename(sotuv_file.filename))
            sotuv_file.save(sotuv_path)
        else:
            existing = find_input_files('sotuv')
            if existing:
                sotuv_path = existing[0]

        if not sotuv_path or not os.path.exists(sotuv_path):
            return jsonify({'error': 'Sotuv cheki fayli topilmadi. Iltimos, Excel faylni tanlang yoki yuklang.'}), 400

        # Qaytarish file
        if qayt_file and qayt_file.filename:
            qayt_path = os.path.join(OUTPUT_DIR, secure_filename(qayt_file.filename))
            qayt_file.save(qayt_path)
        else:
            existing = find_input_files('qaytarish')
            if existing:
                qayt_path = existing[0]

        # Nomenklatura files — multiple files supported
        if nom_file and nom_file.filename:
            np = os.path.join(OUTPUT_DIR, secure_filename(nom_file.filename))
            nom_file.save(np)
            nom_paths = [np]
        else:
            nom_paths = find_all_nomenklatura_files()

        # Load mapping from ALL nomenklatura files
        mapping = load_nomenklatura_mapping(nom_paths) if nom_paths else ({}, {}, {})

        # Process Sotuv
        s_sum, s_grp, s_raw = process_soliq_file(sotuv_path, mapping)
        CURRENT_DATA['sotuv_summary'] = s_sum
        CURRENT_DATA['sotuv_grp'] = s_grp
        CURRENT_DATA['sotuv_raw'] = s_raw

        # Process Qaytarish
        q_sum = None
        q_grp = None
        q_raw = None
        q_rows_list = []
        if qayt_path and os.path.exists(qayt_path):
            q_sum, q_grp, q_raw = process_soliq_file(qayt_path, mapping)
            CURRENT_DATA['qayt_summary'] = q_sum
            CURRENT_DATA['qayt_grp'] = q_grp
            CURRENT_DATA['qayt_raw'] = q_raw
            q_rows_list = q_grp.to_dict(orient='records')
        else:
            CURRENT_DATA['qayt_summary'] = None
            CURRENT_DATA['qayt_grp'] = None
            CURRENT_DATA['qayt_raw'] = None

        # Subtract returns from sales (NET sotuv = sotuv - qaytarish)
        sotuv_net = subtract_returns_from_sales(s_grp, q_grp)
        CURRENT_DATA['sotuv_net'] = sotuv_net

        # Calculate NET summary
        net_sum = float(sotuv_net['Summa'].sum())
        net_vat = float(sotuv_net['QQS'].sum())
        net_products = len(sotuv_net)

        # Adjust card/cash for net (proportional)
        if s_sum['total_sum'] > 0:
            ratio = net_sum / s_sum['total_sum']
        else:
            ratio = 1.0
        net_cash = s_sum['total_cash'] * ratio
        net_card = s_sum['total_card'] * ratio

        net_summary = {
            'total_sum': net_sum,
            'total_cash': net_cash,
            'total_card': net_card,
            'total_vat': net_vat,
            'total_rows': net_products,
            'unique_products': net_products,
        }

        # Generate output files for all 4 modes — NET (sotuv - qaytarish)
        export_to_1c_excel(sotuv_net, os.path.join(OUTPUT_DIR, '1C_Sotuv_PoNomenklaturno.xlsx'),
                          title="1C Продажа (Пономенклатурно)")
        export_to_1c_excel(sotuv_net, os.path.join(OUTPUT_DIR, '1C_Sotuv_PoIKPU.xlsx'),
                          title="1C Продажа (По ИКПУ)")
        export_to_1c_excel(sotuv_net, os.path.join(OUTPUT_DIR, '1C_Sotuv_PoArtikul.xlsx'),
                          title="1C Продажа (По Артикулу)")
        export_to_1c_excel(sotuv_net, os.path.join(OUTPUT_DIR, '1C_Sotuv_PoKod.xlsx'),
                          title="1C Продажа (По Коду номенклатуры)")

        # Qaytarish files (alohida, Vozvrat po cheku uchun)
        if q_grp is not None and not q_grp.empty:
            export_to_1c_excel(q_grp, os.path.join(OUTPUT_DIR, '1C_Qaytarish_PoNomenklaturno.xlsx'),
                              title="1C Возврат (Пономенклатурно)")
            export_to_1c_excel(q_grp, os.path.join(OUTPUT_DIR, '1C_Qaytarish_PoIKPU.xlsx'),
                              title="1C Возврат (По ИКПУ)")
            export_to_1c_excel(q_grp, os.path.join(OUTPUT_DIR, '1C_Qaytarish_PoArtikul.xlsx'),
                              title="1C Возврат (По Артикулу)")
            export_to_1c_excel(q_grp, os.path.join(OUTPUT_DIR, '1C_Qaytarish_PoKod.xlsx'),
                              title="1C Возврат (По Коду номенклатуры)")

        # Return all rows for the web UI
        return jsonify({
            'success': True,
            'sotuv': s_sum,
            'qaytarish': q_sum,
            'net': net_summary,
            'items_sotuv': sotuv_net.to_dict(orient='records'),
            'items_qayt': q_rows_list,
            'sotuv_file_name': os.path.basename(sotuv_path),
            'qayt_file_name': os.path.basename(qayt_path) if qayt_path else None,
            'nom_files': [os.path.basename(f) for f in nom_paths],
            'mapping_stats': {
                'total_nomenklatura': len(mapping[0]) + len(mapping[1]) + len(mapping[2]),
                'by_barcode': len(mapping[0]),
                'by_ikpu': len(mapping[1]),
                'by_name': len(mapping[2])
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<file_type>')
def download(file_type):
    file_map = {
        # Sotuv (NET = sotuv - qaytarish)
        'sotuv_nomenklaturno': '1C_Sotuv_PoNomenklaturno.xlsx',
        'sotuv_ikpu': '1C_Sotuv_PoIKPU.xlsx',
        'sotuv_artikul': '1C_Sotuv_PoArtikul.xlsx',
        'sotuv_kod': '1C_Sotuv_PoKod.xlsx',
        # Qaytarish (alohida Vozvrat po cheku)
        'qayt_nomenklaturno': '1C_Qaytarish_PoNomenklaturno.xlsx',
        'qayt_ikpu': '1C_Qaytarish_PoIKPU.xlsx',
        'qayt_artikul': '1C_Qaytarish_PoArtikul.xlsx',
        'qayt_kod': '1C_Qaytarish_PoKod.xlsx',
    }

    filename = file_map.get(file_type)
    if not filename:
        return jsonify({'error': 'Fayl turi noto\'g\'ri'}), 404

    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        return jsonify({'error': 'Fayl hali yaratilmagan. Avval tahlil qiling.'}), 404

    return send_file(path, as_attachment=True, download_name=filename)

def _run_1c_job(job_id: str, doc_date, send_sotuv: bool, send_qaytarish: bool,
                sotuv_items: list, qayt_items: list):
    """Background threadda 1C ga yuboradi."""
    JOBS[job_id]['status'] = 'running'
    results = {}
    try:
        reset_cache()  # Har safar yangi run uchun cache tozalanadi

        if send_sotuv and sotuv_items:
            JOBS[job_id]['log'] = 'Sotuv ma\'lumoti 1C ga yuborilmoqda...'
            r = create_realization(
                doc_date=doc_date,
                items=sotuv_items,
                doc_number=f'SOLIQ-{doc_date.strftime("%d%m%Y")}'
            )
            results['sotuv'] = r
            if not r.get('success'):
                JOBS[job_id].update({'status': 'error', 'results': results,
                                     'error': f'Sotuv xatosi: {r.get("error","")}'})
                return

        if send_qaytarish and qayt_items:
            JOBS[job_id]['log'] = 'Qaytarish ma\'lumoti 1C ga yuborilmoqda...'
            r = create_return(
                doc_date=doc_date,
                items=qayt_items,
                doc_number=f'VOZVRAT-{doc_date.strftime("%d%m%Y")}'
            )
            results['qaytarish'] = r
        elif send_qaytarish:
            results['qaytarish'] = {'success': True, 'info': 'Qaytarish ma\'lumoti yo\'q'}

        JOBS[job_id].update({'status': 'done', 'results': results})

    except Exception as e:
        import traceback
        JOBS[job_id].update({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        })


@app.route('/api/send_to_1c', methods=['POST'])
def send_to_1c():
    """
    1C ga yuborish — background threadda ishlaydi.
    Darhol job_id qaytaradi. Status /api/send_to_1c/status/<job_id> dan olinadi.
    """
    global CURRENT_DATA
    from datetime import date as date_cls

    body = request.get_json() or {}
    date_str       = body.get('doc_date', str(date_cls.today()))
    send_sotuv     = body.get('send_sotuv', True)
    send_qaytarish = body.get('send_qaytarish', True)

    try:
        doc_date = date_cls.fromisoformat(date_str)
    except Exception:
        doc_date = date_cls.today()

    sotuv_df = CURRENT_DATA.get('sotuv_net')
    if sotuv_df is None or sotuv_df.empty:
        return jsonify({'error': 'Avval faylni tahlil qiling!'}), 400

    sotuv_items = sotuv_df.to_dict(orient='records')
    qayt_df     = CURRENT_DATA.get('qayt_grp')
    qayt_items  = qayt_df.to_dict(orient='records') if (qayt_df is not None and not qayt_df.empty) else []

    job_id = str(_uuid.uuid4())[:8]
    JOBS[job_id] = {'status': 'pending', 'log': 'Navbatda...', 'results': None, 'error': None}

    t = threading.Thread(
        target=_run_1c_job,
        args=(job_id, doc_date, send_sotuv, send_qaytarish, sotuv_items, qayt_items),
        daemon=True
    )
    t.start()

    return jsonify({'job_id': job_id, 'status': 'pending'})


@app.route('/api/send_to_1c/status/<job_id>', methods=['GET'])
def send_to_1c_status(job_id):
    """Job holatini qaytaradi."""
    job = JOBS.get(job_id)
    if not job:
        return jsonify({'error': 'Job topilmadi'}), 404
    return jsonify(job)


if __name__ == '__main__':
    print("Soliq -> 1C Import Web Platformasi ishga tushmoqda...")
    print("Manzil: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)
