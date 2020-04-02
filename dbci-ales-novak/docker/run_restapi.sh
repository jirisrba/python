docker run -p 6000:5000 -v /var/dbci/sha1s:/var/dbci/sha1s:rw -v /u01/data/dbutils/tns:/etc/oracle/wallet --env TZ=Europe/Prague --name dbci-restapi -t dbci-restapi
