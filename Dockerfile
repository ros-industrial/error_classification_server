FROM python:3.6.9

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

ADD src /src

ENTRYPOINT [ "python3" ]