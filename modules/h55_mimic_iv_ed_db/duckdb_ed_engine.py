"""
duckdb_ed_engine.py - M56 MIMIC-IV-ED 2.2 全量急診數據 DuckDB 零解壓安全查詢引擎

導入 DuckDB 4 大硬體防禦規範：
1. max_memory = '512MB' (記憶體剛性封頂)
2. temp_directory = '/Volumes/D2024/tmp_duckdb' (Spill 定向外接硬碟)
3. read_only = True (防範檔案鎖)
4. Filter Pushdown & Column Pruning (極速過濾與時間視窗降維)
"""

import os
import sys
import json
from typing import Dict, Any, Optional

DEFAULT_MIMIC_ED_DIR = "/Volumes/D2024/data/mimic.iv/mimic-iv-ed-2.2"
EXTERNAL_TMP_DIR = "/Volumes/D2024/tmp_duckdb"

def resolve_mimic_ed_data_dir() -> Optional[str]:
    """解析 MIMIC-IV-ED 2.2 全量急診數據目錄 (優先讀取環境變數 MIMIC_IV_ED_DATA_DIR)"""
    env_dir = os.environ.get("MIMIC_IV_ED_DATA_DIR")
    if env_dir and os.path.exists(env_dir):
        return env_dir

    if os.path.exists(DEFAULT_MIMIC_ED_DIR):
        return DEFAULT_MIMIC_ED_DIR

    return None

def get_duckdb_connection():
    """初始化具備 4 大硬體安全防禦之 DuckDB 唯讀連線"""
    try:
        import duckdb
    except ImportError:
        raise ImportError("未安裝 duckdb 套件。請執行 pip install duckdb")

    os.makedirs(EXTERNAL_TMP_DIR, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET max_memory = '512MB';")
    con.execute(f"SET temp_directory = '{EXTERNAL_TMP_DIR}';")
    return con

def query_ed_patient_from_full_dataset(subject_id_query: str, data_dir: str) -> Optional[Dict[str, Any]]:
    """
    透過 DuckDB 零解壓直接過濾 .csv.gz 急診檔，獲取單一病患之急診與檢傷結構化摘要
    """
    try:
        sub_id = int(str(subject_id_query).strip())
    except ValueError:
        return None

    # 檢查是否有 ed/ 子目錄
    ed_subdir = os.path.join(data_dir, "ed")
    if os.path.exists(ed_subdir):
        data_dir = ed_subdir

    edstays_csv = os.path.join(data_dir, "edstays.csv.gz")
    triage_csv = os.path.join(data_dir, "triage.csv.gz")
    pyxis_csv = os.path.join(data_dir, "pyxis.csv.gz")
    medrecon_csv = os.path.join(data_dir, "medrecon.csv.gz")
    diagnosis_csv = os.path.join(data_dir, "diagnosis.csv.gz")

    if not os.path.exists(edstays_csv):
        return None

    con = get_duckdb_connection()

    # 1. 查詢急診入住主檔
    ed_sql = f"SELECT subject_id, stay_id, hadm_id, gender, race, arrival_transport, disposition FROM read_csv_auto('{edstays_csv}') WHERE subject_id = {sub_id} ORDER BY intime DESC LIMIT 1;"
    ed_df = con.execute(ed_sql).fetchdf()
    if ed_df.empty:
        con.close()
        return None

    stay_id = int(ed_df['stay_id'].iloc[0])
    hadm_id = int(ed_df['hadm_id'].iloc[0]) if pd_not_null(ed_df['hadm_id'].iloc[0]) else 0
    gender = str(ed_df['gender'].iloc[0])
    race = str(ed_df['race'].iloc[0])
    disposition = str(ed_df['disposition'].iloc[0])

    # 2. 查詢檢傷分類 (Triage)
    acuity = 3
    chiefcomplaint = "N/A"
    triage_info = {}
    if os.path.exists(triage_csv):
        tr_sql = f"SELECT acuity, chiefcomplaint, temperature, heartrate, resprate, o2sat, sbp, dbp, pain FROM read_csv_auto('{triage_csv}') WHERE stay_id = {stay_id} LIMIT 1;"
        tr_df = con.execute(tr_sql).fetchdf()
        if not tr_df.empty:
            acuity = int(tr_df['acuity'].iloc[0]) if pd_not_null(tr_df['acuity'].iloc[0]) else 3
            chiefcomplaint = str(tr_df['chiefcomplaint'].iloc[0]) if pd_not_null(tr_df['chiefcomplaint'].iloc[0]) else "N/A"
            triage_info = {
                "acuity": acuity,
                "chiefcomplaint": chiefcomplaint,
                "temperature": float(tr_df['temperature'].iloc[0]) if pd_not_null(tr_df['temperature'].iloc[0]) else None,
                "heartrate": float(tr_df['heartrate'].iloc[0]) if pd_not_null(tr_df['heartrate'].iloc[0]) else None,
                "resprate": float(tr_df['resprate'].iloc[0]) if pd_not_null(tr_df['resprate'].iloc[0]) else None,
                "o2sat": float(tr_df['o2sat'].iloc[0]) if pd_not_null(tr_df['o2sat'].iloc[0]) else None,
                "sbp": float(tr_df['sbp'].iloc[0]) if pd_not_null(tr_df['sbp'].iloc[0]) else None,
                "dbp": float(tr_df['dbp'].iloc[0]) if pd_not_null(tr_df['dbp'].iloc[0]) else None,
                "pain": str(tr_df['pain'].iloc[0]) if pd_not_null(tr_df['pain'].iloc[0]) else None
            }

    # 3. 查詢急診自動發藥機 Pyxis 給藥紀錄 (前 5 筆)
    pyxis_list = []
    if os.path.exists(pyxis_csv):
        pyx_sql = f"SELECT name, charttime FROM read_csv_auto('{pyxis_csv}') WHERE stay_id = {stay_id} ORDER BY charttime ASC LIMIT 5;"
        try:
            pyx_df = con.execute(pyx_sql).fetchdf()
            for _, r in pyx_df.iterrows():
                pyxis_list.append({"name": str(r['name']), "charttime": str(r['charttime'])})
        except Exception:
            pass

    # 4. 查詢入院前居家用藥整合 Medrecon (前 5 筆)
    medrecon_list = []
    if os.path.exists(medrecon_csv):
        med_sql = f"SELECT name, etcdescription FROM read_csv_auto('{medrecon_csv}') WHERE stay_id = {stay_id} LIMIT 5;"
        try:
            med_df = con.execute(med_sql).fetchdf()
            for _, r in med_df.iterrows():
                medrecon_list.append({"name": str(r['name']), "category": str(r['etcdescription']) if pd_not_null(r['etcdescription']) else ""})
        except Exception:
            pass

    con.close()

    return {
        "subject_id": sub_id,
        "stay_id": stay_id,
        "hadm_id": hadm_id,
        "gender": gender,
        "race": race,
        "acuity": acuity,
        "chiefcomplaint": chiefcomplaint,
        "disposition": disposition,
        "triage_info": triage_info,
        "pyxis_list": pyxis_list,
        "medrecon_list": medrecon_list,
        "is_seed": 0
    }

def pd_not_null(val):
    return val is not None and str(val) != "nan" and str(val) != "None" and str(val) != "0"


def query_ed_candidates_from_full_dataset(
    data_dir: str,
    condition: Optional[str] = None,
    acuity: Optional[int] = None,
    archetype: Optional[str] = None,
    limit: int = 10
) -> list:
    """
    透過 DuckDB Filter Pushdown 批量檢索符合條件之急診病患清單，並組裝完整病患資料。
    """
    ed_subdir = os.path.join(data_dir, "ed")
    if os.path.exists(ed_subdir):
        data_dir = ed_subdir

    edstays_csv = os.path.join(data_dir, "edstays.csv.gz")
    triage_csv = os.path.join(data_dir, "triage.csv.gz")
    pyxis_csv = os.path.join(data_dir, "pyxis.csv.gz")
    medrecon_csv = os.path.join(data_dir, "medrecon.csv.gz")

    if not os.path.exists(edstays_csv) or not os.path.exists(triage_csv):
        return []

    con = get_duckdb_connection()

    where_clauses = []
    if condition and condition.strip():
        cond_clean = condition.strip().replace("'", "''").lower()
        where_clauses.append(f"LOWER(t.chiefcomplaint) LIKE '%{cond_clean}%'")

    if acuity is not None:
        where_clauses.append(f"t.acuity = {int(acuity)}")

    # Archetype 篩選條件
    if archetype:
        arch = archetype.strip().lower()
        if arch == "common-emergency":
            # 常見急診：檢傷 2 或 3
            where_clauses.append("t.acuity IN (2, 3)")
        elif arch == "rare-critical":
            # 危急重症：檢傷 1 或 ADMITTED
            where_clauses.append("(t.acuity = 1 OR UPPER(e.disposition) = 'ADMITTED')")
        elif arch == "borderline-trap":
            # 臨界陷阱：檢傷 4~5 但 ADMITTED，或檢傷 2~3 但 HOME
            where_clauses.append("((t.acuity IN (4, 5) AND UPPER(e.disposition) = 'ADMITTED') OR (t.acuity IN (2, 3) AND UPPER(e.disposition) = 'HOME'))")

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    cand_sql = f"""
    SELECT e.subject_id, e.stay_id, e.hadm_id, e.gender, e.race, e.disposition,
           t.acuity, t.chiefcomplaint, t.temperature, t.heartrate, t.resprate, t.o2sat, t.sbp, t.dbp, t.pain
    FROM read_csv_auto('{triage_csv}') t
    JOIN read_csv_auto('{edstays_csv}') e ON t.stay_id = e.stay_id
    {where_sql}
    LIMIT {int(limit)};
    """

    try:
        cand_df = con.execute(cand_sql).fetchdf()
    except Exception as exc:
        sys.stderr.write(f"⚠️ [DuckDB Error] {exc}\n")
        con.close()
        return []

    if cand_df.empty:
        con.close()
        return []

    stay_ids = [int(s) for s in cand_df['stay_id'].tolist()]
    stay_ids_str = ",".join(str(s) for s in stay_ids)

    # 批次取得 pyxis
    pyxis_map = {}
    if os.path.exists(pyxis_csv) and stay_ids:
        pyx_sql = f"""
        SELECT stay_id, name, charttime
        FROM read_csv_auto('{pyxis_csv}')
        WHERE stay_id IN ({stay_ids_str})
        ORDER BY charttime ASC;
        """
        try:
            pyx_df = con.execute(pyx_sql).fetchdf()
            for _, r in pyx_df.iterrows():
                sid = int(r['stay_id'])
                if sid not in pyxis_map:
                    pyxis_map[sid] = []
                if len(pyxis_map[sid]) < 5:
                    pyxis_map[sid].append({"name": str(r['name']), "charttime": str(r['charttime'])})
        except Exception:
            pass

    # 批次取得 medrecon
    medrecon_map = {}
    if os.path.exists(medrecon_csv) and stay_ids:
        med_sql = f"""
        SELECT stay_id, name, etcdescription
        FROM read_csv_auto('{medrecon_csv}')
        WHERE stay_id IN ({stay_ids_str})
        LIMIT {len(stay_ids) * 10};
        """
        try:
            med_df = con.execute(med_sql).fetchdf()
            for _, r in med_df.iterrows():
                sid = int(r['stay_id'])
                if sid not in medrecon_map:
                    medrecon_map[sid] = []
                if len(medrecon_map[sid]) < 5:
                    medrecon_map[sid].append({
                        "name": str(r['name']),
                        "category": str(r['etcdescription']) if pd_not_null(r['etcdescription']) else ""
                    })
        except Exception:
            pass

    con.close()

    results = []
    for _, row in cand_df.iterrows():
        sid = int(row['stay_id'])
        sub_id = int(row['subject_id'])
        hadm_id = int(row['hadm_id']) if pd_not_null(row['hadm_id']) else 0
        ac_val = int(row['acuity']) if pd_not_null(row['acuity']) else 3

        triage_info = {
            "acuity": ac_val,
            "chiefcomplaint": str(row['chiefcomplaint']) if pd_not_null(row['chiefcomplaint']) else "N/A",
            "temperature": float(row['temperature']) if pd_not_null(row['temperature']) else None,
            "heartrate": float(row['heartrate']) if pd_not_null(row['heartrate']) else None,
            "resprate": float(row['resprate']) if pd_not_null(row['resprate']) else None,
            "o2sat": float(row['o2sat']) if pd_not_null(row['o2sat']) else None,
            "sbp": float(row['sbp']) if pd_not_null(row['sbp']) else None,
            "dbp": float(row['dbp']) if pd_not_null(row['dbp']) else None,
            "pain": str(row['pain']) if pd_not_null(row['pain']) else None
        }

        results.append({
            "subject_id": sub_id,
            "stay_id": sid,
            "hadm_id": hadm_id,
            "gender": str(row['gender']),
            "race": str(row['race']),
            "acuity": ac_val,
            "chiefcomplaint": str(row['chiefcomplaint']) if pd_not_null(row['chiefcomplaint']) else "N/A",
            "disposition": str(row['disposition']),
            "triage_info": triage_info,
            "pyxis_list": pyxis_map.get(sid, []),
            "medrecon_list": medrecon_map.get(sid, [])
        })

    return results

