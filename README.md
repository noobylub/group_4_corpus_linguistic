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

## Adding Dependencies

Install a new package:
```bash
pip install <package_name>
```

Update requirements.txt:
```bash
pip freeze > requirements.txt
```

## Note

The `venv/` directory is excluded from Git. Clone and run the setup commands above to recreate it.
