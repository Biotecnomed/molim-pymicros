FROM python:3.6.9
WORKDIR /app
COPY requirements.txt requirements.txt
#RUN pip -V
RUN pip install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
#RUN mkdir ./wd
#CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
CMD [ "uwsgi", "--http", "0.0.0.0:8080", "--wsgi-file", "app.py", "--callable", "app", "--processes", "1", "--threads", "4", "--stats", "127.0.0.1:9191"]
