FROM python:3.12-slim

WORKDIR /workspace

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "run.py" ]

EXPOSE 5000