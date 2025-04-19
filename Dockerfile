FROM python:3.12-slim

WORKDIR /app

ENV DISCORD_TOKEN=
ENV NOTIFY_CHANNEL_ID=boll

COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN playwright install

CMD ["python", "script.py"]
