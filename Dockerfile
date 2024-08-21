FROM python:3.12
WORKDIR /app/
COPY requirements.txt .
COPY index.py .
RUN pip install -r requirements.txt
VOLUME /config
CMD ["python", "-u", "index.py", "/config/config.yml"]
