# Z-Truyen Backend Service

Dịch vụ backend cào truyện và cung cấp OPDS 1.2 Feed cho Xteink X3 và KOReader.

## Khởi chạy nhanh

```bash
# Docker Compose
docker compose up -d

# Hoặc chế độ lập trình Python
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8080
```

## Kiểm thử

```bash
pytest
```
