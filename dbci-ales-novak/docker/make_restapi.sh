cp ../DbCiBuildTracker/cz/oracle/DBContinuousIntegration.py rest_api
cd rest_api
docker build . --no-cache -t dbci-restapi
