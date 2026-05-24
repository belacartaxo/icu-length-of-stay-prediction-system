feature_groups = {
    "median_impute": [
        # vitals / physiology
        "systolic_bp_min", "systolic_bp_avg", "systolic_bp_max",
        "diastolic_bp_min", "diastolic_bp_avg", "diastolic_bp_max",
        "heart_rate_min", "heart_rate_avg", "heart_rate_max",
        "respiratory_rate_min", "respiratory_rate_avg", "respiratory_rate_max",
        "temperature_min", "temperature_avg", "temperature_max",
        "spo2_min", "spo2_avg", "spo2_max",
        "fio2_avg", "peep_min", "peep_avg", "peep_max",
        "minute_volume_min", "minute_volume_avg", "minute_volume_max",
        "tidal_volume_min", "tidal_volume_avg", "tidal_volume_max",
        "weight_min", "weight_avg", "weight_max",
        "pain_score_min", "pain_score_avg", "pain_score_max",

        # GCS
        "gcs_verbal_min", "gcs_verbal_avg", "gcs_verbal_max",
        "gcs_eye_min", "gcs_eye_avg", "gcs_eye_max",
        "gcs_motor_min", "gcs_motor_avg", "gcs_motor_max",
        "gcs_total_min", "gcs_total_avg", "gcs_total_max",

        # labs
        "ph_blood_latest", "hematocrit_latest", "hemoglobin_latest",
        "bun_latest", "bicarbonate_latest", "bilirubin_total_latest",
        "calcium_latest", "albumin_latest", "ptt_latest",
        "creatinine_latest", "pt_latest", "po2_latest",
        "glucose_lab_latest", "platelets_latest", "magnesium_latest",
        "lactate_latest", "o2_sat_blood_latest", "chloride_latest",
        "potassium_latest", "pco2_latest", "urine_protein_latest",
        "troponin_latest", "alt_latest", "wbc_latest",
        "total_protein_latest", "urine_creatinine_latest",
        "lipase_latest", "glucose_bedside_avg", "glucose_bedside_max"
    ],

    "zero_impute": [
        # medication / intervention sums
        "d5w_sum", "midazolam_sum", "propofol_sum",
        "phenylephrine_sum", "vasopressin_sum", "epinephrine_sum",
        "morphine_sum", "ffp_sum", "furosemide_sum",
        "heparin_sum", "milrinone_sum", "kcl_sum",
        "dexmedetomidine_sum", "prbc_sum", "dobutamine_sum",
        "tpn_sum", "cisatracurium_sum", "dopamine_sum",
        "lorazepam_sum", "hydromorphone_sum",
        "cryoprecipitate_sum", "metronidazole_sum",
        "piperacillin_tazo_sum", "sodium_bicarbonate_sum",
        "vancomycin_sum", "fentanyl_sum", "platelets_sum",

        # medication / intervention counts
        "d5w_count", "propofol_count", "midazolam_count",
        "fentanyl_count", "epinephrine_count", "phenylephrine_count",
        "heparin_count", "vasopressin_count", "dopamine_count",
        "furosemide_count", "kcl_count", "cisatracurium_count",
        "milrinone_count", "ffp_count", "prbc_count", "tpn_count",
        "dobutamine_count", "morphine_count", "albumin_5_count",
        "lorazepam_count", "hydromorphone_count",
        "piperacillin_tazo_count", "sodium_bicarbonate_count",
        "metronidazole_count", "platelets_count", "vancomycin_count",

        # outputs / drains
        "urine_foley_count", "urine_total_sum", "urine_total_count",
        "gastric_tube_sum", "urine_void_count", "stool_sum",
        "drain_sum", "chest_tube_count", "urine_void_sum",
        "chest_tube_sum", "drain_count", "emesis_sum",
        "gastric_tube_count", "stool_count",

        # lines / procedures
        "arterial_line_num", "icp_line_num", "picc_line_num",
        "trauma_line_num", "dialysis_catheter_num",
        "icp_line_had", "arterial_line_had", "picc_line_had",
        "trauma_line_had", "dialysis_catheter_had"
    ],

    "do_not_impute": [
        "EXPIRE_FLAG"
    ],

    "drop_from_training": [
        "SUBJECT_ID"
    ]
}