# python newmap.py --data_dir data/

import os
import argparse
import pandas as pd
from config.config import MIMIC_DIR, MAP_FILE_PATH


CHARTEVENTS_SEARCH = {
    # Vitais
    "heart_rate":         ["heart rate"],
    "systolic_bp":        ["systolic", "arterial bp", "nbp sys", "abp sys"],
    "diastolic_bp":       ["diastolic", "abp dias", "nbp dias"],
    "map":                ["mean arterial", "map"],
    "respiratory_rate":   ["respiratory rate", "resp rate"],
    "temperature":        ["temperature"],
    "spo2":               ["spo2", "o2 sat", "oxygen saturation"],
    # GCS
    "gcs_total":          ["gcs total", "gcs - total"],
    "gcs_motor":          ["gcs motor", "motor response"],
    "gcs_verbal":         ["gcs verbal", "verbal response"],
    "gcs_eye":            ["gcs eye", "eye opening"],
    # Respiratório
    "fio2":               ["fio2", "fraction of inspired o2", "inspired o2 fraction"],
    "peep":               ["peep", "positive end expiratory"],
    "tidal_volume":       ["tidal volume"],
    "minute_volume":      ["minute volume"],
    "peak_insp_pressure": ["peak insp pressure", "peak inspiratory pressure"],
    # Metabólico
    "glucose_bedside":    ["glucose finger", "glucose (70-105)", "fingerstick glucose"],
    "capillary_refill":   ["capillary refill"],
    # Antropométrico
    "weight":             ["admit wt", "daily weight", "weight (kg)"],
    "height":             ["height"],
    # Neurológico
    "pupil_right":        ["pupil right"],
    "pupil_left":         ["pupil left"],
    "pain_score":         ["pain score", "pain level"],
}

OUTPUTEVENTS_SEARCH = {
    "urine_foley":        ["urine out foley", "foley"],
    "urine_void":         ["urine out void", "void"],
    "urine_condom":       ["urine out condom", "condom cath"],
    "urine_nephrostomy":  ["nephrostomy"],
    "urine_suprapubic":   ["suprapubic"],
    "urine_total":        ["urine", "ileoconduit"],
    "stool":              ["stool", "fecal", "colostomy", "ileostomy", "rectal tube"],
    "emesis":             ["emesis", "vomit"],
    "gastric_tube":       ["gastric tube", "nasogastric", "oral gastric", "anderson"],
    "chest_tube":         ["chest tube", "pleural"],
    "dialysis_out":       ["dialysis out", "hemodialysis", "peritoneal dialysis"],
    "drain":              ["jackson pratt", "hemovac", "wound vac", "drain out"],
    "csf":                ["csf", "cerebrospinal"],
}

INPUTEVENTS_SEARCH = {
    # Vasopressores
    "norepinephrine":     ["norepinephrine", "noradrenaline", "levophed"],
    "epinephrine":        ["epinephrine", "adrenaline"],
    "phenylephrine":      ["phenylephrine", "neosynephrine"],
    "vasopressin":        ["vasopressin"],
    "dopamine":           ["dopamine"],
    # Inotropos
    "dobutamine":         ["dobutamine"],
    "milrinone":          ["milrinone"],
    # Sedação e Analgesia
    "propofol":           ["propofol"],
    "midazolam":          ["midazolam", "versed"],
    "fentanyl":           ["fentanyl"],
    "morphine":           ["morphine"],
    "ketamine":           ["ketamine"],
    "dexmedetomidine":    ["dexmedetomidine", "precedex"],
    "lorazepam":          ["lorazepam", "ativan"],
    "hydromorphone":      ["hydromorphone", "dilaudid"],
    # Relaxantes musculares
    "cisatracurium":      ["cisatracurium"],
    "vecuronium":         ["vecuronium"],
    "rocuronium":         ["rocuronium"],
    # Insulina
    "insulin_regular":    ["insulin regular"],
    "insulin_glargine":   ["insulin glargine", "lantus"],
    "insulin_nph":        ["insulin nph"],
    "insulin_humalog":    ["insulin humalog"],
    # Hemoderivados
    "prbc":               ["packed red blood", "prbc"],
    "platelets":          ["platelet"],
    "ffp":                ["fresh frozen plasma", "ffp"],
    "cryoprecipitate":    ["cryoprecipitate"],
    # Colóides e Albumina
    "albumin_25":         ["albumin 25%"],
    "albumin_5":          ["albumin 5%"],
    "hetastarch":         ["hetastarch", "hespan"],
    # Cristalóides
    "normal_saline":      ["0.9% sodium chloride", "normal saline", "ns "],
    "lr":                 ["lactated ringers", "lactated ringer"],
    "d5w":                ["dextrose 5%", "d5w"],
    "d10w":               ["dextrose 10%"],
    "d50":                ["dextrose 50%"],
    # Nutrição
    "tpn":                ["tpn", "total parenteral"],
    "enteral":            ["ensure", "nutren", "impact", "peptamen"],
    # Antibióticos
    "vancomycin":         ["vancomycin"],
    "meropenem":          ["meropenem"],
    "piperacillin_tazo":  ["piperacillin", "pip/tazo", "zosyn"],
    "cefepime":           ["cefepime", "maxipime"],
    "ceftriaxone":        ["ceftriaxone", "rocephin"],
    "metronidazole":      ["metronidazole", "flagyl"],
    "fluconazole":        ["fluconazole", "diflucan"],
    # Outros
    "heparin":            ["heparin"],
    "furosemide":         ["furosemide", "lasix"],
    "sodium_bicarbonate": ["sodium bicarbonate", "nahco3"],
    "kcl":                ["potassium chloride", "kcl"],
}

LABEVENTS_SEARCH = {
    # Hemograma
    "wbc":                ["white blood cells", "leukocytes"],
    "hemoglobin":         ["hemoglobin"],
    "hematocrit":         ["hematocrit"],
    "platelets":          ["platelet count"],
    # Função renal
    "creatinine":         ["creatinine"],
    "bun":                ["urea nitrogen"],
    # Electrólitos
    "sodium":             ["sodium"],
    "potassium":          ["potassium"],
    "chloride":           ["chloride"],
    "bicarbonate":        ["bicarbonate"],
    "calcium":            ["calcium, total", "calcium total"],
    "magnesium":          ["magnesium"],
    "phosphate":          ["phosphate"],
    # Função hepática
    "bilirubin_total":    ["bilirubin, total", "bilirubin total"],
    "alt":                ["alanine aminotransferase"],
    "ast":                ["aspartate aminotransferase"],
    "alp":                ["alkaline phosphatase"],
    "albumin":            ["albumin"],
    # Coagulação
    "inr":                ["inr", "pt - inr"],
    "pt":                 ["pt", "prothrombin time"],
    "ptt":                ["ptt", "partial thromboplastin"],
    # Gasometria
    "ph_blood":           ["ph"],
    "lactate":            ["lactate"],
    "po2":                ["po2", "partial pressure of oxygen"],
    "pco2":               ["pco2", "partial pressure of co2"],
    "o2_sat_blood":       ["oxygen saturation"],
    # Outros
    "glucose_lab":        ["glucose"],
    "troponin":           ["troponin"],
    "crp":                ["c reactive protein", "crp"],
    "procalcitonin":      ["procalcitonin"],
    "total_protein":      ["total protein"],
    "lipase":             ["lipase"],
    "amylase":            ["amylase"],
    "urine_glucose":      ["glucose, urine", "glucose - urine"],
    "urine_protein":      ["protein, urine", "protein - urine"],
    "urine_creatinine":   ["creatinine, urine"],
}

DATETIMEEVENTS_SEARCH = {
    # Diálise
    "dialysis":           ["last dialysis", "dialysis"],
    # Linhas arteriais
    "arterial_line":      ["arterial line insertion", "a-line insertion"],
    # Linhas centrais
    "central_line":       ["central line insertion", "central venous line"],
    # PICC
    "picc_line":          ["picc line insertion", "picc insertion"],
    # Trauma
    "trauma_line":        ["trauma line insertion"],
    # Midline
    "midline":            ["midline insertion"],
    # ICP
    "icp_line":           ["icp line insertion", "intracranial pressure"],
    # Outros
    "dialysis_catheter":  ["dialysis catheter insertion"],
    "tandem_heart":       ["tandem heart"],
    "swan_ganz":          ["swan ganz", "pulmonary artery catheter"],
    "epidural":           ["epidural insertion"],
    "chest_tube_insert":  ["chest tube insertion date"],
}


def load_d_items(data_dir):
    path = os.path.join(data_dir, "D_ITEMS.csv")
    if not os.path.exists(path):
        print(f"D_ITEMS.csv não encontrado em {path}")
        return None
    df = pd.read_csv(path)
    df.columns = df.columns.str.upper()
    df["LABEL"] = df["LABEL"].fillna("").str.lower()
    df["CATEGORY"] = df["CATEGORY"].fillna("").str.lower()
    df["DBSOURCE"] = df.get("DBSOURCE", pd.Series([""] * len(df))).fillna("").str.lower()
    print(f"D_ITEMS carregado: {len(df)} items")
    return df


def load_d_labitems(data_dir):
    path = os.path.join(data_dir, "D_LABITEMS.csv")
    if not os.path.exists(path):
        print(f"D_LABITEMS.csv não encontrado em {path}")
        return None
    df = pd.read_csv(path)
    df.columns = df.columns.str.upper()
    df["LABEL"] = df["LABEL"].fillna("").str.lower()
    df["CATEGORY"] = df["CATEGORY"].fillna("").str.lower()
    df["FLUID"] = df["FLUID"].fillna("").str.lower()
    print(f"D_LABITEMS carregado: {len(df)} items")
    return df


def search_items(df, keywords, search_cols=["LABEL"]):
    mask = pd.Series([False] * len(df))
    for kw in keywords:
        for col in search_cols:
            mask |= df[col].str.contains(kw, case=False, na=False)
    return sorted(df[mask]["ITEMID"].tolist())


def print_categories(df, source_filter=None, title="Categorias disponíveis"):
    print(f"\n{title}")
    if source_filter:
        df = df[df["DBSOURCE"] == source_filter]
    for cat, count in df["CATEGORY"].value_counts().items():
        print(f"  {cat:<35} ({count:>5} items)")


def build_map(df, search_config, source_filter=None):
    if source_filter:
        df = df[df["DBSOURCE"].str.contains(source_filter, na=False)]
    return {
        feature: search_items(df, keywords)
        for feature, keywords in search_config.items()
    }


def preview_map(feature_map, df, max_per_feature=5):
    print()
    for feature, ids in feature_map.items():
        if not ids:
            print(f"{feature:<30} → nenhum id encontrado")
            continue
        labels = df[df["ITEMID"].isin(ids)]["LABEL"].tolist()[:max_per_feature]
        print(f"{feature:<30} → {ids[:max_per_feature]}  ({labels})")


def generate_map_py(chart_map, output_map, input_map, lab_map, datetime_map, output_path):
    def fmt_dict(d, indent=4):
        pad = " " * indent
        lines = []
        for k, v in d.items():
            if v:
                lines.append(f'{pad}"{k}": {v},')
            else:
                lines.append(f'{pad}# "{k}": [],  # nenhum id encontrado, verificar manualmente')
        return "\n".join(lines)

    content = f'''"""
map_auto.py — Gerado automaticamente por newmap.py

Mapeamentos construídos a partir dos dicionários oficiais do MIMIC-III:
  - D_ITEMS.csv     -> CHARTEVENTS, OUTPUTEVENTS, INPUTEVENTS_MV, INPUTEVENTS_CV, DATETIMEEVENTS
  - D_LABITEMS.csv  -> LABEVENTS
"""


CHARTEVENTS_FEATURES_MAP = {{
{fmt_dict(chart_map)}
}}


OUTPUTEVENTS_FEATURES_MAP = {{
{fmt_dict(output_map)}
}}


# MIMIC-III tem dois sistemas de registo de inputs:
#   - INPUTEVENTS_MV.csv  -> MetaVision (doentes a partir de ~2008, ITEMIDs > 220000)
#   - INPUTEVENTS_CV.csv  -> CareVue (doentes mais antigos, ITEMIDs < 220000)

INPUTEVENTS_FEATURES_MAP = {{
{fmt_dict(input_map)}
}}

INPUTEVENTS_MV_FEATURES_MAP = INPUTEVENTS_FEATURES_MAP
INPUTEVENTS_CV_FEATURES_MAP = INPUTEVENTS_FEATURES_MAP


LABEVENTS_FEATURES_MAP = {{
{fmt_dict(lab_map)}
}}


# DATETIMEEVENTS — datas de inserção de linhas e procedimentos.
# O valor não é numérico mas sim uma data, por isso a feature gerada
# é binária: o doente tinha esta linha nas primeiras 24h? (0/1)
# Usar build_event_occurrence_feature_table em vez de build_numeric_feature_table.

DATETIMEEVENTS_FEATURES_MAP = {{
{fmt_dict(datetime_map)}
}}


# MICROBIOLOGYEVENTS não usa ITEMIDs.
# Filtrar directamente por texto nas colunas:
#   SPEC_TYPE_DESC  -> tipo de amostra
#   ORG_NAME        -> organismo identificado
#   AB_NAME         -> antibiótico testado
#   INTERPRETATION  -> S=Sensível, R=Resistente, I=Intermédio

MICROBIOLOGY_SPECIMEN_TYPES = [
    "BLOOD CULTURE",
    "URINE",
    "SPUTUM",
    "BRONCHOALVEOLAR LAVAGE",
    "WOUND SWAB",
    "CATHETER TIP-IV",
    "CSF;SPINAL FLUID",
    "PLEURAL FLUID",
    "PERITONEAL FLUID",
]

MICROBIOLOGY_ORGANISMS_OF_INTEREST = [
    "STAPHYLOCOCCUS AUREUS",
    "STAPHYLOCOCCUS, COAGULASE NEGATIVE",
    "KLEBSIELLA PNEUMONIAE",
    "ESCHERICHIA COLI",
    "PSEUDOMONAS AERUGINOSA",
    "ENTEROCOCCUS SP.",
    "CANDIDA ALBICANS",
    "ACINETOBACTER BAUMANNII",
    "ENTEROBACTER CLOACAE",
    "STREPTOCOCCUS PNEUMONIAE",
]

MICROBIOLOGY_RESISTANCE_MARKERS = {{
    "mrsa": {{"organism": "STAPHYLOCOCCUS AUREUS",  "antibiotic": "OXACILLIN",   "result": "R"}},
    "vre":  {{"organism": "ENTEROCOCCUS SP.",        "antibiotic": "VANCOMYCIN",  "result": "R"}},
    "esbl": {{"organism": "KLEBSIELLA PNEUMONIAE",   "antibiotic": "CEFTRIAXONE", "result": "R"}},
    "cre":  {{"organism": "KLEBSIELLA PNEUMONIAE",   "antibiotic": "MEROPENEM",   "result": "R"}},
}}
'''

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\nmap_auto.py gerado em: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Gera map_auto.py a partir dos dicionários do MIMIC-III")
    parser.add_argument("--data_dir", default=MIMIC_DIR)
    parser.add_argument("--output", default=MAP_FILE_PATH)
    args = parser.parse_args()

    d_items    = load_d_items(args.data_dir)
    d_labitems = load_d_labitems(args.data_dir)

    if d_items is None and d_labitems is None:
        print("Para gerar map_auto.py com ITEMIDs reais, fornece --data_dir com D_ITEMS.csv e D_LABITEMS.csv")
        return

    if d_items is not None:
        print_categories(d_items, title="D_ITEMS — todas as categorias")
        print_categories(d_items, source_filter="metavision", title="D_ITEMS — MetaVision")
        print_categories(d_items, source_filter="carevue", title="D_ITEMS — CareVue")

        print("\n[CHARTEVENTS] A construir mapeamento...")
        chart_map = build_map(d_items, CHARTEVENTS_SEARCH)
        preview_map(chart_map, d_items)

        print("\n[OUTPUTEVENTS] A construir mapeamento...")
        output_map = build_map(d_items, OUTPUTEVENTS_SEARCH)
        preview_map(output_map, d_items)

        print("\n[INPUTEVENTS] A construir mapeamento...")
        input_map = build_map(d_items, INPUTEVENTS_SEARCH)
        preview_map(input_map, d_items)

        print("\n[DATETIMEEVENTS] A construir mapeamento...")
        datetime_map = build_map(d_items, DATETIMEEVENTS_SEARCH)
        preview_map(datetime_map, d_items)
    else:
        chart_map    = {k: [] for k in CHARTEVENTS_SEARCH}
        output_map   = {k: [] for k in OUTPUTEVENTS_SEARCH}
        input_map    = {k: [] for k in INPUTEVENTS_SEARCH}
        datetime_map = {k: [] for k in DATETIMEEVENTS_SEARCH}

    if d_labitems is not None:
        print_categories(d_labitems, title="D_LABITEMS — todas as categorias")

        print("\nFluidos em D_LABITEMS:")
        for fluid, count in d_labitems["FLUID"].value_counts().items():
            print(f"  {fluid:<20} ({count} items)")

        print("\n[LABEVENTS] A construir mapeamento...")
        lab_map = build_map(d_labitems, LABEVENTS_SEARCH)
        preview_map(lab_map, d_labitems)
    else:
        lab_map = {k: [] for k in LABEVENTS_SEARCH}

    generate_map_py(chart_map, output_map, input_map, lab_map, datetime_map, args.output)

    found = lambda m: sum(1 for v in m.values() if v)
    print(f"""
CHARTEVENTS   : {found(chart_map)}/{len(chart_map)} features com ITEMIDs
OUTPUTEVENTS  : {found(output_map)}/{len(output_map)} features com ITEMIDs
INPUTEVENTS   : {found(input_map)}/{len(input_map)} features com ITEMIDs
LABEVENTS     : {found(lab_map)}/{len(lab_map)} features com ITEMIDs
DATETIMEEVENTS: {found(datetime_map)}/{len(datetime_map)} features com ITEMIDs
MICROBIOLOGY  : mapeamento por texto (sem ITEMIDs)

Output: {args.output}
""")


if __name__ == "__main__":
    main()