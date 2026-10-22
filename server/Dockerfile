FROM python:3.12-slim
WORKDIR /app
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y libxcb1 libx11-6 libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "from rapidocr_onnxruntime import RapidOCR; RapidOCR()" || true
COPY requirements-tts.txt .
RUN pip install --no-cache-dir --no-deps -r requirements-tts.txt
COPY app ./app
VOLUME /data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
