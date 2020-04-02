#FROM ubuntu:16.04
FROM python:3
 
# Update OS
#RUN sed -i 's/# \(.*multiverse$\)/\1/g' /etc/apt/sources.list
#RUN apt-get update
#RUN apt-get -y upgrade

# Add requirements.txt
ADD requirements.txt .
 
# Install app requirements
ARG https_proxy=http://www-proxy-ams.nl.oracle.com:80
RUN pip install -r requirements.txt
RUN rm -f requirements.txt
 
WORKDIR /opt

ADD instantclient-basic-linux.x64-12.2.0.1.0.tar.bz2 .
ADD libaio1_0.3.110-3_amd64.deb .
RUN dpkg -i libaio1_0.3.110-3_amd64.deb
RUN rm libaio1_0.3.110-3_amd64.deb

ENV LD_LIBRARY_PATH=/opt/instantclient_12_2/
ENV ORACLE_HOME=/opt/instantclient_12_2/
ENV TNS_ADMIN=/etc/oracle/wallet/

# Create app directory
WORKDIR /webapp
ADD DBContinuousIntegration.py .
 
# Set the default directory for our environment
ENV HOME /webapp

#WORKDIR /
#RUN ls -l /webapp
#WORKDIR /webapp

# Expose port 8000 for uwsgi
#EXPOSE 8000
 
#ENTRYPOINT ["uwsgi", "--http", "0.0.0.0:8000", "--module", "app:app", "--processes", "1", "--threads", "8"]
#ENTRYPOINT ["uwsgi", "--http", "0.0.0.0:8000", "--wsgi-file", "committracker.py", "--processes", "1", "--threads", "8"]
#

ENTRYPOINT ["python"]
CMD ["DBContinuousIntegration.py"]
