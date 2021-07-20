FROM python:3.7
RUN pip install fastapi uvicorn requests psycopg2 python-multipart google-api-python-client google-auth-oauthlib google-auth-httplib2
EXPOSE 80 6969
COPY ./app /app
WORKDIR /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]