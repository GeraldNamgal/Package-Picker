FROM python:3.7-slim
ARG CLIENT_ID
ARG CLIENT_SECRET
ARG DB_USER
ARG DB_HOST
ARG DB_PORT
ARG DB_DATABASE
ARG DB_PASSWORD
ARG DOMAIN_NAME

ENV PYTHONUNBUFFERED 1
ENV CLIENT_ID $CLIENT_ID
ENV CLIENT_SECRET $CLIENT_SECRET
ENV DB_USER $DB_USER
ENV DB_HOST $DB_HOST
ENV DB_PORT $DB_PORT
ENV DB_DATABASE $DB_DATABASE
ENV DB_PASSWORD $DB_PASSWORD
ENV DOMAIN_NAME $DOMAIN_NAME

RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
EXPOSE 80
CMD python manage.py runserver 0.0.0.0:80
