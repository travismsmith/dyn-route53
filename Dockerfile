FROM python:3-alpine

RUN apk add --update python3
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY dyn-route53.py dyn-route53.py
ENTRYPOINT [ "./dyn-route53.py" ]
