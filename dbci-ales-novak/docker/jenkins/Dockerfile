FROM jenkins/jenkins:lts

#RUN wget -Y off -O /tmp/apache-maven-3.2.2.tar.gz http://archive.apache.org/dist/maven/maven-3/3.2.2/binaries/apache-maven-3.2.2-bin.tar.gz
#RUN curl --proxy $https_proxy http://archive.apache.org/dist/maven/maven-3/3.2.2/binaries/apache-maven-3.2.2-bin.tar.gz > /tmp/apache-maven-3.2.2.tar.gz

WORKDIR /opt

USER root
ADD apache-maven-3.2.2-bin.tar.gz .
RUN ln -s /opt/apache-maven-3.2.2 /opt/maven
RUN ln -s /opt/maven/bin/mvn /usr/local/bin
ENV MAVEN_HOME /opt/maven

WORKDIR /
ADD sqlcl-17.3.0.271.1943-no-jre.zip /opt/
WORKDIR /opt
RUN unzip sqlcl-17.3.0.271.1943-no-jre.zip
RUN rm -f sqlcl-17.3.0.271.1943-no-jre.zip

WORKDIR /

ADD jdk-8u151-linux-x64.tar.gz /opt/
#RUN tar xfz /opt/jdk-8u151-linux-x64.tar.gz -C /opt/
#RUN rm /opt/jdk-8u151-linux-x64.tar.gz

WORKDIR /

ADD instantclient-basic-linux.x64-12.2.0.1.0.zip /opt/
WORKDIR /opt
RUN unzip instantclient-basic-linux.x64-12.2.0.1.0.zip
RUN rm instantclient-basic-linux.x64-12.2.0.1.0.zip

ADD libaio1_0.3.110-3_amd64.deb /opt/
RUN dpkg -i /opt/libaio1_0.3.110-3_amd64.deb
RUN rm /opt/libaio1_0.3.110-3_amd64.deb

USER jenkins

WORKDIR /var/jenkins_home
ENV PATH $PATH:/opt/maven/bin:/opt/sqlcl/bin
ENV JAVA_HOME /opt/jdk1.8.0_151
ENV LD_LIBRARY_PATH=/opt/instantclient_12_2/
ENV TNS_ADMIN /etc/oracle/wallet
