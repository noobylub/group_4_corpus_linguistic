# Corpus Linguistic

## Setup

1. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## To Run 

Run HS_hansard
```bash
python HS_hansard/good_hscript.py
```
Two new files 
- hansard_kwics_only.csv
- hansard_result.csv

Notes 
- You must modify the directory to the correct directory location
```bash
hansard_dir = "/Users/muhammadmushoffa/Desktop/corpus_linguistic/Hansard 2000 file sample"

kwics_file = "/Users/muhammadmushoffa/Desktop/corpus_linguistic/hansard_kwics_only.csv"

complete_kwics_file = "/Users/muhammadmushoffa/Desktop/corpus_linguistic/hansard_results.csv"
```
