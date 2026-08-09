from pathlib import Path
import csv, hashlib, importlib.util, json, math, shutil, subprocess, sys

def install_and_run_colabfold():
    if not RUN_COLABFOLD:
        print('RUN_COLABFOLD=False；跳过 ColabFold。')
        return
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--no-warn-conflicts', 'colabfold[alphafold-minus-jax] @ git+https://github.com/sokrypton/ColabFold'], check=True)
    subprocess.run(['bash', '-lc', 'rm -f /usr/local/lib/python3.*/dist-packages/tensorflow/core/kernels/libtfkernel_sobol_op.so /usr/local/lib/python3.*/dist-packages/tensorflow/lite/python/*/*.so 2>/dev/null || true'], check=True)
    spec = importlib.util.find_spec('colabfold.batch')
    if spec and spec.origin:
        batch_path = Path(spec.origin)
        batch_source = batch_path.read_text(encoding='utf-8')
        old = 'scores[k] = np.around(conf[-1][k], 2).item()'
        if old in batch_source:
            batch_path.write_text(batch_source.replace(old, 'scores[k] = float(conf[-1][k])'), encoding='utf-8')
        else:
            print('Note: ColabFold score-rounding line was not found; continuing without patch.')
    from colabfold.colabfold import run_mmseqs2
    from colabfold.input import msa_to_str
    from colabfold.batch import run
    from colabfold.download import download_alphafold_params
    from colabfold.utils import setup_logging
    work_dir = USER_OUT / 'colabfold_work'
    msa_dir = work_dir / 'msa'
    prediction_dir = work_dir / 'predictions'
    msa_dir.mkdir(parents=True, exist_ok=True)
    prediction_dir.mkdir(parents=True, exist_ok=True)
    unique_sequences = list(unique_non_de_novo)
    msa_by_sequence = {}
    if unique_sequences:
        digest = hashlib.sha1('\n'.join(unique_sequences).encode()).hexdigest()[:12]
        msas = run_mmseqs2(unique_sequences, str(msa_dir / f'unique_{digest}'), use_env=COLABFOLD_USE_ENV, use_filter=COLABFOLD_USE_FILTER, use_templates=False, use_pairing=False, host_url=COLABFOLD_MSA_SERVER, user_agent='LigandMPNN-ColabFold-pipeline/1.1')
        if len(unique_sequences) == 1 and isinstance(msas, str):
            msas = [msas]
        if len(msas) != len(unique_sequences):
            raise RuntimeError('MSA 返回数量不一致。')
        msa_by_sequence = dict(zip(unique_sequences, msas))
    queries = []
    for candidate in CANDIDATES:
        chain_sequences = list(candidate['chain_sequences'].values())
        unpaired_msa = [f'>101\n{sequence}\n' if chain == COLABFOLD_DE_NOVO_CHAIN else msa_by_sequence[sequence] for chain, sequence in candidate['chain_sequences'].items()]
        query_only = [f'>101\n{sequence}\n' for sequence in chain_sequences]
        a3m = msa_to_str(unpaired_msa=unpaired_msa, paired_msa=query_only, query_seqs_unique=chain_sequences, query_seqs_cardinality=[1] * len(chain_sequences))
        queries.append((candidate['jobname'], chain_sequences, [a3m], None))
    recycles = None if COLABFOLD_NUM_RECYCLES == 'auto' else int(COLABFOLD_NUM_RECYCLES)
    tolerance = None if COLABFOLD_RECYCLE_EARLY_STOP_TOLERANCE == 'auto' else float(COLABFOLD_RECYCLE_EARLY_STOP_TOLERANCE)
    max_msa = None if COLABFOLD_MAX_MSA == 'auto' else COLABFOLD_MAX_MSA
    data_dir = Path('/content/colabfold_params')
    data_dir.mkdir(exist_ok=True)
    setup_logging(work_dir / 'colabfold.log')
    download_alphafold_params(COLABFOLD_MODEL_TYPE, data_dir)
    run(queries=queries, result_dir=prediction_dir, use_templates=False, custom_template_path=None, num_relax=0, msa_mode='custom', model_type=COLABFOLD_MODEL_TYPE, num_models=3, num_recycles=recycles, relax_max_iterations=0, recycle_early_stop_tolerance=tolerance, num_seeds=COLABFOLD_NUM_SEEDS, use_dropout=COLABFOLD_USE_DROPOUT, model_order=[1, 2, 3], is_complex=True, data_dir=data_dir, keep_existing_results=False, rank_by='auto', pair_mode='unpaired', pairing_strategy='greedy', stop_at_score=100.0, prediction_callback=None, input_features_callback=None, dpi=100, zip_results=False, save_all=False, max_msa=max_msa, use_cluster_profile=not ('multimer' in COLABFOLD_MODEL_TYPE and max_msa is not None), save_recycles=False, user_agent='LigandMPNN-ColabFold-pipeline/1.1', calc_extra_ptm=True, skip_output=['plots', 'pae_json', 'msa'])
    score_files = sorted(prediction_dir.rglob('*scores*.json'))
    rows = []
    for candidate in CANDIDATES:
        model_scores = []
        for score_file in score_files:
            if score_file.name.startswith(candidate['jobname']) or candidate['jobname'] in str(score_file.parent):
                score_data = json.loads(score_file.read_text(encoding='utf-8'))

                def finite_score(key):
                    try:
                        value = float(score_data.get(key))
                        return value if math.isfinite(value) else None
                    except (TypeError, ValueError):
                        return None
                iptm = finite_score('iptm')
                ptm = finite_score('ptm')
                model_scores.append((iptm if iptm is not None else ptm, iptm, ptm))
        if model_scores:
            _, iptm, ptm = max(model_scores, key=lambda item: item[0] if item[0] is not None else float('-inf'))
        else:
            iptm = None
            ptm = None
            print('Warning: no scores for', candidate['jobname'])
        rows.append({'de_novo_sequence': candidate['de_novo_sequence'], 'total_sequence': candidate['total_sequence'], 'iptm': iptm, 'ptm': ptm, 'sort_value': iptm if iptm is not None else ptm})
    rows.sort(key=lambda item: (item['sort_value'] is not None, item['sort_value'] if item['sort_value'] is not None else float('-inf')), reverse=True)
    final_csv = USER_OUT / COLABFOLD_FINAL_CSV_NAME
    fields = ['de_novo_sequence', 'total_sequence', 'iptm', 'ptm'] if COLABFOLD_DE_NOVO_CHAIN else ['total_sequence', 'iptm', 'ptm']
    with final_csv.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            output = {key: row.get(key) for key in fields}
            for key in ('iptm', 'ptm'):
                output[key] = '' if output[key] is None else f'{output[key]:.6f}'
            writer.writerow(output)
    print(final_csv.read_text(encoding='utf-8')[:5000])
    if COLABFOLD_DELETE_INTERMEDIATES:
        shutil.rmtree(work_dir, ignore_errors=True)
    if DOWNLOAD_FINAL_CSV:
        files.download(str(final_csv))
install_and_run_colabfold()
