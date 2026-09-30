FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir '.[api]'
ENV INTENT_CACHE_DIR=/data/llm-cache
VOLUME ["/data"]
EXPOSE 8000
CMD ["uvicorn", "intent_labeler.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
