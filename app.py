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
