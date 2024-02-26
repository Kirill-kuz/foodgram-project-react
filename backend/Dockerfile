FROM python:latest
WORKDIR /app
COPY requirements.txt . 
# RUN pip install -r requirements.txt --no-cache-dir
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:9080", "foodgram.wsgi"]
