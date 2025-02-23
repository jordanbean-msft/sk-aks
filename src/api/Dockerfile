FROM python:3.12

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN opentelemetry-bootstrap -a install

COPY ./app /code/app

CMD [ "opentelemetry-instrument", "--logs_exporter", "otlp", "python", "-m", "uvicorn", "app.main:app", "--loop", "asyncio", "--host", "0.0.0.0", "--port", "80"]
#CMD [ "opentelemetry-instrument", "--logs_exporter", "otlp", "python", "-m", "uvicorn", "app.main:app"]

#CMD [ "fastapi", "run", "app/main.py", "--port", "80"]

#CMD [ "opentelemetry-instrument", "--logs_exporter", "otlp", "fastapi", "run", "app/main.py", "--port", "80"]