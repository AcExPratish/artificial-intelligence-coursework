## Setup

```bash
git clone https://github.com/AcExPratish/artificial-intelligence-coursework.git
cd artificial-intelligence-coursework
git lfs install
git lfs pull

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running

The notebook (`implementation.ipynb`) is already executed and includes all
outputs and figures. To re-run it from scratch:

```bash
python data_preparation.py         # ~40 s — downloads + slices 500K reviews
python metadata_preparation.py     # ~10 min — filters product metadata
jupyter notebook implementation.ipynb
```

The two scripts populate `dataset/` with the CSVs the notebook reads. They
stream the source files from Hugging Face, so neither downloads the full
22 GB Electronics review dump.

## Files

```
data_preparation.py       Slice 500K Amazon Electronics reviews
metadata_preparation.py   Filter product metadata to ASINs we kept
implementation.ipynb      Main notebook — EDA, sentiment, recommendation
dataset/                  Reviews + metadata CSVs (generated locally)
figures/                  PNG plots used in the report
artifacts/                Result CSVs (sentiment, recommendation, cold-start)
requirements.txt          Python dependencies
```

## Dataset

Amazon Reviews 2023, Electronics subset, McAuley Lab.
<https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023>

Not bundled with the submission — run the two preparation scripts to recreate
the CSVs locally.

## Environment

Python ≥ 3.9. Tested on macOS (Apple Silicon, MPS backend for PyTorch).
Should run on Linux/Windows with CPU or CUDA without changes.
