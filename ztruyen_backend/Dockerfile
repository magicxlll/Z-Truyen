FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e ".[dev]"
COPY . .
EXPOSE 8080
CMD ["uvicorn", "ztruyen_backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
