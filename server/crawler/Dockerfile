FROM python:3.12-slim
WORKDIR /crawler
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["scrapy", "list"]
