import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INPUT_PATH = "data/datasets/diagnosis_value_counts_full.csv"
OUTPUT_PATH = "data/datasets/diagnosis_map.csv"

BATCH_SIZE = 50
MAX_WORKERS = 10
SAVE_EVERY_BATCHES = 10

CATEGORIES = [
    "cardiovascular",
    "respiratory",
    "infectious",
    "neurological",
    "gastrointestinal",
    "renal",
    "endocrine_metabolic",
    "hematologic",
    "oncology",
    "trauma_injury",
    "musculoskeletal",
    "psychiatric",
    "pregnancy_obstetric",
    "genitourinary",
    "dermatologic",
    "hepatobiliary",
    "toxicology_poisoning",
    "postoperative_surgical",
    "symptoms_unspecified",
    "other"
]


def save_progress(results, output_path):
    results_df = pd.DataFrame(results)
    results_df = results_df.drop_duplicates(subset=["diagnosis"], keep="last")
    results_df.to_csv(output_path, index=False)
    print(f"Progress saved: {len(results_df)} diagnoses classified.")


def classify_diagnosis_batch(diagnoses, max_retries=3):
    prompt = f"""
Classify each medical diagnosis into exactly one of these categories:

{CATEGORIES}

If a diagnosis fits multiple categories, choose the most clinically dominant condition.

Return only valid JSON in this format:
{{
  "results": [
    {{"diagnosis": "...", "category": "..."}}
  ]
}}

Diagnoses:
{json.dumps(diagnoses, ensure_ascii=False)}
"""

    for attempt in range(max_retries):
        try:
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt,
                text={
                    "format": {
                        "type": "json_object"
                    }
                }
            )

            content = response.output_text.strip()

            if not content:
                raise ValueError("Empty response from OpenAI API.")

            parsed_response = json.loads(content)

            if "results" not in parsed_response:
                raise ValueError(f"Missing 'results' key: {parsed_response}")

            return parsed_response["results"]

        except Exception as error:
            print(f"Attempt {attempt + 1} failed: {error}")

            if attempt == max_retries - 1:
                raise error

            time.sleep(2 ** attempt)


def classify_all_diagnoses_parallel(
    df,
    diagnosis_col="DIAGNOSIS",
    batch_size=BATCH_SIZE,
    max_workers=MAX_WORKERS,
    save_every_batches=SAVE_EVERY_BATCHES,
    output_path=OUTPUT_PATH
):
    unique_diagnoses = (
        df[diagnosis_col]
        .dropna()
        .astype(str)
        .str.strip()
        .drop_duplicates()
        .tolist()
    )

    existing_results = []

    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        existing_results = existing_df.to_dict("records")
        already_classified = set(existing_df["diagnosis"].astype(str))
        print(f"Loaded existing progress: {len(already_classified)} diagnoses.")
    else:
        already_classified = set()

    diagnoses_to_classify = [
        diagnosis for diagnosis in unique_diagnoses
        if diagnosis not in already_classified
    ]

    batches = [
        diagnoses_to_classify[i:i + batch_size]
        for i in range(0, len(diagnoses_to_classify), batch_size)
    ]

    print(f"Total diagnoses: {len(unique_diagnoses)}")
    print(f"Remaining diagnoses: {len(diagnoses_to_classify)}")
    print(f"Total batches to run: {len(batches)}")

    all_results = existing_results.copy()
    completed_batches = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_batch = {
            executor.submit(classify_diagnosis_batch, batch): batch
            for batch in batches
        }

        for future in as_completed(future_to_batch):
            batch = future_to_batch[future]

            try:
                results = future.result()
                all_results.extend(results)

                completed_batches += 1
                print(f"Finished batch {completed_batches}/{len(batches)}")

                if completed_batches % save_every_batches == 0:
                    save_progress(all_results, output_path)

            except Exception as error:
                print("Batch failed:")
                print(batch)
                print(error)

    save_progress(all_results, output_path)

    return pd.DataFrame(all_results).drop_duplicates(
        subset=["diagnosis"],
        keep="last"
    )


df = pd.read_csv(INPUT_PATH)

diagnosis_map = classify_all_diagnoses_parallel(
    df,
    diagnosis_col="DIAGNOSIS"
)

print(diagnosis_map.head())