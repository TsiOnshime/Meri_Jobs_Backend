FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# No EXPOSE -- this process doesn't serve HTTP either, it long-polls the
# match.found Kafka topic and pre-generates/caches mock interview
# questions for matched jobs (see prep/consumers/match_found_consumer.py).
CMD ["python", "manage.py", "consume_match_found"]