FROM prioreg.azurecr.io/prio-data/uvicorn_deployment:2.1.0

COPY ./requirements.txt /
RUN pip install -r requirements.txt 

COPY ./restfiles/* /home/gunicorn/restfiles/
WORKDIR /home/gunicorn
ENV GUNICORN_APP="restfiles.app:app"
