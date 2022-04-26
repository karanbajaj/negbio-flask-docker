# Using the Ubuntu image (our OS)
FROM ubuntu:latest
# Update package manager (apt-get) 
# and install (with the yes flag `-y`)
# Python and Pip
RUN apt-get -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false update
RUN apt-get install -y python3.9 nano
RUN apt-get install -y python3-pip 
RUN apt-get install -y git-all

RUN apt-get install python-is-python3
RUN apt install -y python3.8-venv python-pkg-resources
RUN apt-get install -y default-jre
RUN git clone -b python3 https://github.com/karanbajaj/NegBio.git
WORKDIR /NegBio
RUN python -m venv negbio_env
RUN pip install -r requirements.txt
RUN python setup.py install --user
RUN python -c "from bllipparser import RerankingParser; RerankingParser.fetch_and_load('GENIA+PubMed')"
RUN apt-get -y install nginx
ENV STATIC_URL /static
ENV STATIC_PATH /var/www/app/static
RUN apt-get install -y  python3-dev build-essential libssl-dev libffi-dev python3-setuptools
RUN pip install uwsgi flask
COPY ./app /NegBio
CMD [ "python" , "./main.py" ]