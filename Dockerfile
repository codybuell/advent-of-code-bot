FROM python:3.11-alpine

COPY crontab .
COPY advent-of-code-bot.py .
COPY requirements.txt .

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN crontab crontab
RUN python3 -m venv $VIRTUAL_ENV
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "crond", "-f" ]
