# Docker support
This is a updated version of the current docker support.
Container support is only for development purposes and should not be used in production without your own modificatins.

It's not needed to reload the container after you make changes in your current branch.

Images are currently not available in docker hub or other repository, so you have to build them yourself.

After a successful launch PowerDNS-Admin is reachable at http://localhost:9393

PowerDNS runs op port localhost udp/5353


## Basic commands:
### Build images
cd to this directory

```# ./build-images.sh```

### Run containers
Build the images before you run this command.

```# docker-compose up```

### Stop containers
```# docker-compose stop```

### Remove containers
```# docker-compose rm```
