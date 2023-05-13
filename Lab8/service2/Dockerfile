FROM python:3.9

WORKDIR /app

COPY . .
# COPY requirements.txt .
RUN pip install -r requirements.txt
# COPY service2.py .
# COPY POI.txt .

CMD [ "python", "-u", "service2.py" ]
