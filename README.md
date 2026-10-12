# CITAR-NER-Br

**CITAR-NER-Br** is a dataset for fine-grained legal citation named entity recognition (NER) in Brazilian Portuguese. This repository provides the dataset, processed data files for the baseline systems evaluated in the accompanying paper, baseline model outputs, and evaluation scripts.

> **Paper:** *CITAR-NER-Br: A Unified NER Dataset for Fine-Grained Legal Citation Extraction in Brazilian Portuguese*  
> **Publication:** EMNLP 2026  
> **Paper URL:** `[To be added]`
>
> Please refer to the paper for the dataset construction procedure, annotation details, chunking methodology, experimental setup, and full results.

## Repository structure

```text
.
├── CITAR-NER-Br/
│   ├── verif_gpt.py
│   ├── raw_data/
│   │   ├── lener/
│   │   └── tesemo/
│   └── parsed/
│       ├── docs/
│       │   ├── lener/
│       │   ├── tesemo/
│       │   ├── final_train.json
│       │   ├── final_dev.json
│       │   └── final_test.json
│       └── chunks/
│           ├── lener/
│           ├── tesemo/
│           ├── final_bart_train.txt
│           ├── final_bart_dev.txt
│           ├── final_bart_test.txt
│           ├── final_w2_train.json
│           ├── final_w2_dev.json
│           └── final_w2_test.json
└── models/
    ├── outputs/
    │   ├── w2ner/
    │   ├── bart-ner/
    │   ├── promptner-chatgpt/
    │   └── promptner-gemini/
    ├── results/
    │   ├── eval.py
    │   ├── *_matches.json
    │   └── *_results.json
    ├── prompt_with_negs.txt
    └── request-llm.py
```

*The tree above is a simplified overview; some subdirectories contain additional files and dataset-specific splits.*

## Dataset files

### `CITAR-NER-Br/raw_data/`

Contains the data exported directly from the BRAT annotation tool, organized by source sub-collection:

- `lener/` — LeNER-Br ([https://github.com/peluz/lener-br](https://github.com/peluz/lener-br)) documents and annotations.
- `tesemo/` — Ulysses Tesemõ ([https://github.com/ulysses-camara/ulysses-tesemo](https://github.com/ulysses-camara/ulysses-tesemo)) documents and annotations, separated into 2 Brazilian courts (STJ and TRF5).

The raw annotation exports include the original text and corresponding annotation files.

### `CITAR-NER-Br/parsed/docs/`

Contains the parsed document-level data, organized by source sub-collection (`lener/` and `tesemo/`) and by the complete CITAR-NER-Br collection (`final_*.json` files).

The split construction (train, dev and test files) and processing procedure are described in **Section 4.2** of the paper.

### `CITAR-NER-Br/parsed/chunks/`

Contains the chunks generated from the parsed documents in `parsed/docs/`, following the procedure described in **Section 4.3** of the paper.

These files are formatted for direct use as inputs in the non-LLM baseline methods evaluated in the paper:

- **W²NER:** `final_w2_*.json`
- **BART-NER:** `final_bart_*.txt`

### `CITAR-NER-Br/verif_gpt.py`

Script implementing the LLM-based verification step described in **Section 3.4** of the paper.

## Baseline outputs and evaluation

### `models/outputs/`

Contains the outputs produced by the baseline configurations evaluated in the paper:

- W²NER
- BART-NER
- PromptNER with ChatGPT
- PromptNER with Gemini

Each baseline output directory contains the output generated using the corresponding baseline implementation as presented in its original code repository, along with a `format.py` script. This script converts the baseline output into a `final_*.json` file formatted for the evaluation pipeline in `models/results/`.

The PromptNER output directories also contain `parse_responses.py`, an intermediate script used to parse raw LLM responses.

### `models/results/`

Contains the evaluation script and the result files for the four baseline configurations.

- `eval.py` reads the formatted prediction files in `models/outputs/` and generates the entity matches and evaluation metrics.
- `*_matches.json` records exact matches between gold entities and predicted entities.
- `*_results.json` contains the metrics calculated from those matches.
- Files containing `_disc` in their names refer specifically to matches and results for the subset containing only **discontinuous entities**.

## Running the LLM prompt

### `models/prompt_with_negs.txt`

Contains the NER prompt adapted from PromptNER and used for the LLM-based baseline experiments.

### `models/request-llm.py`

Script used to call the Gemini and ChatGPT APIs with the prompt above.

Before running the script, replace the `API-KEY` placeholders with your own API keys. Keep API keys private and do not commit them to version control. API access may incur costs, depending on your provider and account.

## Reproducing the evaluation

For evaluation using the provided baseline predictions:

1. Locate the relevant baseline configuration under `models/outputs/`.
2. If starting from the original baseline output, use that directory's `format.py` to convert the predictions into the format expected by the evaluation pipeline.
3. Run `models/results/eval.py` in an environment with its required Python dependencies available.
4. Inspect the generated `*_matches.json` and `*_results.json` files.

The exact training and inference commands, dependencies, and environment setup may vary by baseline implementation. Please also consult the original repositories:

- **W²NER:** [https://github.com/ljynlp/w2ner](https://github.com/ljynlp/w2ner)
- **BART-NER:** [https://github.com/yhcc/BARTNER](https://github.com/yhcc/BARTNER)

> **Compatibility note:** These baseline implementations were released with older library and framework versions. Because dependencies and APIs evolve over time, some code changes may be necessary to install or run them in a current environment.

## Reference our paper

If you use CITAR-NER-Br in your research, please cite our paper. The BibTeX entry below is a placeholder; replace it with the final bibliographic information when available.

```bibtex
@inproceedings{citarnerbr2026,
  title     = {CITAR-NER-Br: A Unified NER Dataset for Fine-Grained Legal Citation Extraction in Brazilian Portuguese},
  author    = {Author Names},
  booktitle = {Proceedings of the 2026 Conference on Empirical Methods in Natural Language Processing},
  year      = {2026}
}
```

## License

See [`LICENSE.md`](LICENSE.md) for the repository's license and usage terms.
