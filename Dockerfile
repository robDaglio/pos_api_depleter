FROM kitchenbrains/centos7python379

LABEL project="POS API Acceptance Test"
LABEL maintainer="mail@mailer.com"

RUN mkdir /usr/src/app
WORKDIR /usr/src/app

RUN /usr/local/bin/python3.7 -m pip install --upgrade pip
RUN rm -rf ~/.cache/pip
COPY . /usr/src/app

RUN /usr/local/bin/python3.7 -m pip install -r requirements.txt
CMD ["/usr/local/bin/python3.7", "/usr/src/app/deplete.py"]