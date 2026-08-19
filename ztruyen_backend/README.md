# Z-Truyen X3 Backend

Vietnamese online story discovery va download cho Xteink X3.

## Features

- OPDS catalog voi storya.click va Con Duong Ba Chu
- EPUB generation (1 chapter per file)
- Vietnamese language support
- CrossVi/CrossPoint OPDS client compatible

## Quick Start

### 1. Install Dependencies
```bash
cd ztruyen_backend
pip install -e ".[dev]"
```

### 2. Start Server
```bash
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080
```

### 3. Configure X3/CrossVi Simulator
1. Settings > OPDS
2. Add Server: `http://<YOUR_IP>:8080/opds`
3. Browse va download EPUBs

## For Mac mini Deployment
Xem `docs/simulator-setup.md`

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /healthz` | Health check |
| `GET /opds` | Root catalog |
| `GET /opds/search?q=` | Search |
| `GET /opds/book/{id}` | Book detail |
| `GET /opds/download/{chapter_id}` | Download EPUB |

## Testing
```bash
pytest tests/ -v
```

## Project Structure

```
ztruyen_backend/
├── __init__.py
├── main.py
├── mock_data.py
├── opds_renderer.py
├── epub_builder.py
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── README.md
├── sources/
│   ├── __init__.py
│   ├── base.py
│   ├── storya.py
│   └── conduongbachu.py
├── static/
│   └── .gitkeep
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_opds.py
    ├── test_storya.py
    └── test_conduongbachu.py
```

## Supported Sources

### storya.click
- Popular Vietnamese story platform
- OPDS feed: `http://storya.click/opds`

### Con Duong Ba Chu
- Classic Vietnamese web novel source
- OPDS feed: `http://condiduongbachu.com/opds`
