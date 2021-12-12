FROM python:3.9.7-buster

WORKDIR /app
COPY ./code /app
ENTRYPOINT ["/bin/sh", "-l", "-c"]

RUN unlink /etc/localtime
RUN ln -s /usr/share/zoneinfo/Europe/Moscow /etc/localtime
RUN pip uninstall requests

RUN pip install --no-cache -r /app/requirements.txt

CMD ["python /app/main.py"]
