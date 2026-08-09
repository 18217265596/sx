"""LigandMPNN multi-checkpoint/multi-temperature → per-FASTA extract → ColabFold.

This script is executed by LigandMPNN_Colab_Complete_v3.ipynb and reads
the user-visible parameters from the notebook global namespace.
"""
from pathlib import Path
from collections import OrderedDict
import csv
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys

def parse_multi(value, cast, name):
    """Parse one value, comma-separated values, or a Python collection."""
    if isinstance(value, (list, tuple, set)):
        raw = list(value)
    elif isinstance(value, (int, float)):
        raw = [value]
    else:
        raw = [item.strip() for item in str(value).replace('，', ',').split(',') if item.strip()]
    if not raw:
        raise ValueError(f'{name} 不能为空。')
    try:
        parsed = [cast(item) for item in raw]
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{name} 含无法解析的值：{raw}') from exc
    return list(dict.fromkeys(parsed))

def validate_parameters():
    global TASK_CHECKPOINT_ID_LIST
    global TEMPERATURE_LIST
    global NUMBER_OF_BATCHES
    global RUN_COMBINATIONS
    TASK_CHECKPOINT_ID_LIST = parse_multi(TASK_CHECKPOINT_IDS, int, 'TASK_CHECKPOINT_IDS')
    TEMPERATURE_LIST = parse_multi(TEMPERATURES, float, 'TEMPERATURES')
    bad = [value for value in TASK_CHECKPOINT_ID_LIST if value not in range(1, 15)]
    if bad:
        raise ValueError(f'主任务 checkpoint 只能为 1–14；错误编号：{bad}')
    if any((not math.isfinite(value) or value <= 0 for value in TEMPERATURE_LIST)):
        raise ValueError('temperature 必须为正的有限数值。')
    if not isinstance(SEQUENCES_PER_COMBINATION, int) or isinstance(SEQUENCES_PER_COMBINATION, bool) or SEQUENCES_PER_COMBINATION < 1:
        raise ValueError('SEQUENCES_PER_COMBINATION 必须为正整数。')
    if not isinstance(BATCH_SIZE, int) or isinstance(BATCH_SIZE, bool) or BATCH_SIZE < 1:
        raise ValueError('BATCH_SIZE 必须为正整数。')
    if SEQUENCES_PER_COMBINATION % BATCH_SIZE:
        raise ValueError('SEQUENCES_PER_COMBINATION 必须能被 BATCH_SIZE 整除，以保证每个组合精确生成指定数量。')
    NUMBER_OF_BATCHES = SEQUENCES_PER_COMBINATION // BATCH_SIZE
    if FIXED_RESIDUES.strip() and REDESIGNED_RESIDUES.strip():
        raise ValueError('FIXED_RESIDUES 与 REDESIGNED_RESIDUES 不能同时使用。')
    if not isinstance(EXTRACT_TOP_N_PER_FASTA, int) or isinstance(EXTRACT_TOP_N_PER_FASTA, bool) or EXTRACT_TOP_N_PER_FASTA < 1:
        raise ValueError('EXTRACT_TOP_N_PER_FASTA 必须为正整数。')
    if COLABFOLD_MAX_BINDERS is not None and int(COLABFOLD_MAX_BINDERS) < 1:
        raise ValueError('COLABFOLD_MAX_BINDERS 必须为 None 或正整数。')
    if COLABFOLD_MODEL_TYPE != 'alphafold2_multimer_v3':
        raise ValueError('模型固定为 alphafold2_multimer_v3。')
    if COLABFOLD_NUM_MODELS != 3 or COLABFOLD_MODEL_ORDER != [1, 2, 3]:
        raise ValueError('固定使用模型 1、2、3。')
    if COLABFOLD_NUM_RELAX != 0:
        raise ValueError('当前流程不做 Amber relaxation。')
    if not COLABFOLD_CALC_EXTRA_PTM:
        raise ValueError('请保持 COLABFOLD_CALC_EXTRA_PTM=True。')
    if isinstance(COLABFOLD_NUM_RECYCLES, str) and COLABFOLD_NUM_RECYCLES != 'auto':
        raise ValueError("COLABFOLD_NUM_RECYCLES 只能为整数或 'auto'。")
    RUN_COMBINATIONS = [(checkpoint_id, temperature) for checkpoint_id in TASK_CHECKPOINT_ID_LIST for temperature in TEMPERATURE_LIST]
    print('\n参数解析结果')
    print(' checkpoint:', TASK_CHECKPOINT_ID_LIST)
    print(' temperature:', TEMPERATURE_LIST)
    print(' 组合数:', len(RUN_COMBINATIONS))
    print(' 每个组合生成:', SEQUENCES_PER_COMBINATION)
    print(' 理论生成总数:', len(RUN_COMBINATIONS) * SEQUENCES_PER_COMBINATION)
    print(' 每个 FASTA 提取:', EXTRACT_TOP_N_PER_FASTA)

def install_ligandmpnn():
    global MODEL_DIR
    global EXTRACT_PY
    if ROOT.exists():
        shutil.rmtree(ROOT)
    subprocess.run(['git', 'clone', '--depth', '1', 'https://github.com/dauparas/LigandMPNN.git', str(ROOT)], check=True)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--upgrade', 'ProDy==2.6.1', 'biopython>=1.81', 'ml-collections==0.1.1', 'dm-tree==0.1.8'], check=True)
    MODEL_DIR = ROOT / 'model_params'
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(['bash', str(ROOT / 'get_model_params.sh'), str(MODEL_DIR)], check=True)
    downloaded = {path.name for path in MODEL_DIR.glob('*.pt')}
    expected = {item[1] for item in CHECKPOINT_OPTIONS.values()}
    missing = sorted(expected - downloaded)
    if missing:
        raise RuntimeError('缺少权重：' + ', '.join(missing))
    for path in MODEL_DIR.glob('*.pt'):
        if path.stat().st_size < 1024 ** 2:
            raise RuntimeError(f'权重文件疑似不完整：{path}')
    os.environ['TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD'] = '1'
    run_py = ROOT / 'run.py'
    source = run_py.read_text(encoding='utf-8')
    source = source.replace('torch.load(checkpoint_path, map_location=device)', 'torch.load(checkpoint_path, map_location=device, weights_only=False)')
    source = source.replace('torch.load(args.checkpoint_path_sc, map_location=device)', 'torch.load(args.checkpoint_path_sc, map_location=device, weights_only=False)')
    run_py.write_text(source, encoding='utf-8')
    if 'checkpoint_path, map_location=device, weights_only=False' not in run_py.read_text(encoding='utf-8'):
        raise RuntimeError('torch.load 补丁失败。')
    aliases = {'\\bnp\\.int\\b': 'int', '\\bnp\\.float\\b': 'float', '\\bnp\\.bool\\b': 'bool', '\\bnp\\.object\\b': 'object', '\\bnp\\.str\\b': 'str', '\\bnp\\.complex\\b': 'complex'}
    for path in ROOT.rglob('*.py'):
        old = path.read_text(encoding='utf-8')
        new = old
        for pattern, replacement in aliases.items():
            new = re.sub(pattern, replacement, new)
        if new != old:
            path.write_text(new, encoding='utf-8')
    EXTRACT_PY = ROOT / 'extract.py'
    subprocess.run(['wget', '-q', 'https://raw.githubusercontent.com/18217265596/sx/master/extract.py', '-O', str(EXTRACT_PY)], check=True)
    if not EXTRACT_PY.exists() or EXTRACT_PY.stat().st_size == 0:
        raise RuntimeError('extract.py 下载失败。')
    print('LigandMPNN ready.')

def temperature_tag(value):
    return f'{value:.10g}'.replace('-', 'm').replace('.', 'p')

def run_ligandmpnn_matrix():
    """Run every checkpoint × temperature and extract Top N per FASTA."""
    global USER_OUT
    global MERGED_EXTRACT_TSV
    global MERGED_EXTRACT_FASTA
    global CANDIDATES
    global unique_non_de_novo
    USER_OUT = ROOT / 'outputs' / USER_PDB.stem
    runs_dir = USER_OUT / 'ligandmpnn_runs'
    per_fasta_dir = USER_OUT / EXTRACT_PER_FASTA_DIR_NAME
    shutil.rmtree(USER_OUT, ignore_errors=True)
    runs_dir.mkdir(parents=True, exist_ok=True)
    per_fasta_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_flags = {'protein_mpnn': '--checkpoint_protein_mpnn', 'ligand_mpnn': '--checkpoint_ligand_mpnn', 'soluble_mpnn': '--checkpoint_soluble_mpnn', 'per_residue_label_membrane_mpnn': '--checkpoint_per_residue_label_membrane_mpnn', 'global_label_membrane_mpnn': '--checkpoint_global_label_membrane_mpnn'}
    environment = os.environ.copy()
    environment['PYTHONUNBUFFERED'] = '1'
    environment['TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD'] = '1'
    extracted_records = []
    processed_fastas = []
    for index, (checkpoint_id, temperature) in enumerate(RUN_COMBINATIONS, 1):
        model_type, checkpoint_name, _ = CHECKPOINT_OPTIONS[checkpoint_id]
        run_name = f'ckpt_{checkpoint_id:02d}_{Path(checkpoint_name).stem}_T_{temperature_tag(temperature)}'
        run_output = runs_dir / run_name
        command = [sys.executable, '-u', 'run.py', '--model_type', model_type, checkpoint_flags[model_type], str(MODEL_DIR / checkpoint_name), '--seed', str(SEED), '--pdb_path', str(USER_PDB), '--out_folder', str(run_output), '--batch_size', str(BATCH_SIZE), '--number_of_batches', str(NUMBER_OF_BATCHES), '--temperature', str(temperature), '--parse_atoms_with_zero_occupancy', str(PARSE_ATOMS_WITH_ZERO_OCCUPANCY), '--save_stats', str(SAVE_STATS), '--verbose', str(VERBOSE)]
        if CHAINS_TO_DESIGN.strip():
            command += ['--chains_to_design', CHAINS_TO_DESIGN.strip()]
        if FIXED_RESIDUES.strip():
            command += ['--fixed_residues', FIXED_RESIDUES.strip()]
        if REDESIGNED_RESIDUES.strip():
            command += ['--redesigned_residues', REDESIGNED_RESIDUES.strip()]
        if PACK_SIDE_CHAINS:
            command += ['--pack_side_chains', '1', '--checkpoint_path_sc', str(MODEL_DIR / CHECKPOINT_OPTIONS[15][1]), '--number_of_packs_per_design', str(NUMBER_OF_PACKS_PER_DESIGN)]
        print('\n' + '=' * 100)
        print(f'Combination {index}/{len(RUN_COMBINATIONS)}')
        print(f'checkpoint={checkpoint_id}; temperature={temperature}')
        print(' '.join(command))
        print('=' * 100)
        result = subprocess.run(command, cwd=ROOT, env=environment, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(result.stdout)
        if result.returncode:
            raise RuntimeError(f'LigandMPNN 运行失败：checkpoint={checkpoint_id}, temperature={temperature}')
        fasta_files = sorted((run_output / 'seqs').glob(EXTRACT_SOURCE_GLOB))
        if not fasta_files:
            raise FileNotFoundError(f'{run_name} 未找到 FASTA。')
        for fasta_path in fasta_files:
            extract_result = subprocess.run([sys.executable, str(EXTRACT_PY), '--input', str(fasta_path), '--top', str(EXTRACT_TOP_N_PER_FASTA)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if extract_result.returncode:
                print(extract_result.stderr)
                raise RuntimeError(f'extract.py 失败：{fasta_path}')
            per_fasta_tsv = per_fasta_dir / f'{run_name}__{fasta_path.stem}.top{EXTRACT_TOP_N_PER_FASTA}.tsv'
            per_fasta_tsv.write_text(extract_result.stdout, encoding='utf-8')
            count = 0
            for line in extract_result.stdout.splitlines():
                if not line.strip():
                    continue
                source_rank, confidence, record_id, total_sequence = line.split('\t', 3)
                try:
                    confidence_value = float(confidence)
                except ValueError:
                    confidence_value = float('-inf')
                extracted_records.append({'checkpoint_id': checkpoint_id, 'checkpoint_name': checkpoint_name, 'temperature': temperature, 'source_run': run_name, 'source_fasta': fasta_path.name, 'source_rank': int(source_rank), 'record_id': record_id, 'overall_confidence': confidence_value, 'total_sequence': total_sequence.strip().upper()})
                count += 1
            processed_fastas.append(fasta_path)
            print(f'{fasta_path.name}: extracted {count}')
    if not extracted_records:
        raise RuntimeError('所有 FASTA 均未提取到候选序列。')
    extracted_records.sort(key=lambda item: (math.isfinite(item['overall_confidence']), item['overall_confidence'] if math.isfinite(item['overall_confidence']) else float('-inf')), reverse=True)
    merged_records = []
    seen_sequences = set()
    for item in extracted_records:
        sequence = item['total_sequence']
        if sequence in seen_sequences:
            continue
        seen_sequences.add(sequence)
        merged_records.append(item)
    if COLABFOLD_MAX_BINDERS is not None:
        merged_records = merged_records[:int(COLABFOLD_MAX_BINDERS)]
    if not merged_records:
        raise RuntimeError('合并与全局去重后没有候选序列。')
    MERGED_EXTRACT_TSV = USER_OUT / EXTRACT_TSV_NAME
    fields = ['global_rank', 'overall_confidence', 'checkpoint_id', 'checkpoint_name', 'temperature', 'source_run', 'source_fasta', 'source_rank', 'record_id', 'total_sequence']
    with MERGED_EXTRACT_TSV.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\t')
        writer.writeheader()
        for rank, item in enumerate(merged_records, 1):
            row = {key: item.get(key) for key in fields}
            row['global_rank'] = rank
            if not math.isfinite(item['overall_confidence']):
                row['overall_confidence'] = ''
            writer.writerow(row)
    MERGED_EXTRACT_FASTA = USER_OUT / EXTRACT_MERGED_FASTA_NAME
    with MERGED_EXTRACT_FASTA.open('w', encoding='utf-8') as handle:
        for rank, item in enumerate(merged_records, 1):
            handle.write(f">rank={rank}, checkpoint_id={item['checkpoint_id']}, temperature={item['temperature']}, overall_confidence={item['overall_confidence']}\n{item['total_sequence']}\n")
    print('\nCombination/extraction summary')
    print(' combinations:', len(RUN_COMBINATIONS))
    print(' FASTA files processed:', len(processed_fastas))
    print(' candidates before global dedup:', len(extracted_records))
    print(' unique candidates for ColabFold:', len(merged_records))
    print(' merged manifest:', MERGED_EXTRACT_TSV)
    print(' merged FASTA:', MERGED_EXTRACT_FASTA)
    records = [{'rank': rank, 'total_sequence': item['total_sequence']} for rank, item in enumerate(merged_records, 1)]
    designed_chains = {item.strip() for item in CHAINS_TO_DESIGN.split(',') if item.strip()} or set(PDB_CHAIN_ORDER)
    if designed_chains - set(PDB_CHAIN_ORDER):
        raise ValueError('CHAINS_TO_DESIGN 包含不存在的链。')
    valid_amino_acids = set('ACDEFGHIKLMNPQRSTVWY')
    CANDIDATES = []
    for record in records:
        parts = [part.strip().upper() for part in record['total_sequence'].split(':')]
        if len(parts) != len(PDB_CHAIN_ORDER):
            raise ValueError(f"rank={record['rank']} 链数与 PDB 不一致。")
        chain_sequences = OrderedDict(zip(PDB_CHAIN_ORDER, parts))
        for chain, sequence in chain_sequences.items():
            if len(sequence) != len(PDB_CHAIN_SEQUENCES[chain]):
                raise ValueError(f"rank={record['rank']} chain {chain} 长度不一致。")
            if set(sequence) - valid_amino_acids:
                raise ValueError(f"rank={record['rank']} chain {chain} 含非法字符。")
            if chain not in designed_chains and sequence != PDB_CHAIN_SEQUENCES[chain]:
                raise ValueError(f"rank={record['rank']} 固定 chain {chain} 与 PDB 不一致；请检查链顺序。")
        total_sequence = ':'.join(parts)
        job_name = f"{COLABFOLD_JOB_PREFIX}_{record['rank']:03d}_{hashlib.sha1(total_sequence.encode()).hexdigest()[:8]}"
        CANDIDATES.append({'jobname': job_name, 'total_sequence': total_sequence, 'chain_sequences': chain_sequences, 'de_novo_sequence': chain_sequences.get(COLABFOLD_DE_NOVO_CHAIN) if COLABFOLD_DE_NOVO_CHAIN else None})
    unique_non_de_novo = OrderedDict()
    for chain in PDB_CHAIN_ORDER:
        if chain == COLABFOLD_DE_NOVO_CHAIN:
            continue
        values = OrderedDict(((candidate['chain_sequences'][chain], None) for candidate in CANDIDATES))
        print(f'chain {chain}: {len(values)} unique sequence(s) requiring MSA')
        for sequence in values:
            unique_non_de_novo.setdefault(sequence, None)
    print('Total unique MSA queries:', len(unique_non_de_novo))
validate_parameters()
install_ligandmpnn()
run_ligandmpnn_matrix()
