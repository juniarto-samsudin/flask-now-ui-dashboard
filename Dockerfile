FROM python:3.7

ENV FLASK_APP run.py

#COPY run.py gunicorn-cfg.py requirements.txt config.py .env ./
#COPY app app
#COPY migrations migrations

COPY run.py gunicorn-cfg.py requirements.txt config.json device-config.json ./
COPY app app
RUN pip install -r requirements.txt
RUN apt-get install -y wget

EXPOSE 5005
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "run:app"]
