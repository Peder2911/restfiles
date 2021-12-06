FROM prioreg.azurecr.io/prio-data/uvicorn_deployment:2.1.0

COPY ./requirements.txt /
RUN pip install -r requirements.txt 

COPY ./views_cache/* /home/gunicorn/views_cache/
WORKDIR /home/gunicorn
ENV GUNICORN_APP="views_cache.app:app"
