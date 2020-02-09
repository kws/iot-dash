# IoT Dashboard

This is a simple companion to the [Hue Controller](https://github.com/kws/hue-controller) 
that displays sensor data captured using the [CSVLooger](https://github.com/kws/hue-controller/blob/master/src/helpers/csvlogger.js). 

Set the environment variable `IOT_DIR` to point at the location of your CSV logfiles. 

## Docker Image

When using the [Docker image](https://hub.docker.com/repository/docker/kajws/iot-dash), 
mount your CSV logfile directory as /data in the container:

```
docker run -d --restart=always --name=iot-dash -p 8080:8080 \
    -v <YOUR DATA PATH HERE>:/data \
    kajws/iot-dash:latest
```

## Todo

 * More sensor types
 * Time ranges to avoid explosion once I have a bit more than a few days of data
 * Configurable dashboards
 * Database back-end
