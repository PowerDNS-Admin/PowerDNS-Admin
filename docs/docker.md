# PowerDNS-Admin packaged by [Azorian Solutions](https://azorian.solutions)

The PowerDNS-Admin is a simple web GUI for managing zone configurations of a PowerDNS Authoritative server.

The PowerDNS-Admin app does NOT modify the PowerDNS Authoritative server database directly. Instead, it communicates with the PDNS server via the built-in HTTP API.

The app does have a database for identity management, access control, and caching which can be hosted in either MySQL or SQLite.

- [PowerDNS-Admin GitHub](https://github.com/ngoduykhanh/PowerDNS-Admin)
- [PowerDNS-Admin Settings](https://github.com/ngoduykhanh/PowerDNS-Admin/blob/master/docs/settings.md)
- [PowerDNS-Admin Wiki](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki)

## Quick reference

- **Maintained by:** [Matt Scott](https://github.com/AzorianSolutions)
- **Github:** [https://github.com/AzorianSolutions](https://github.com/AzorianSolutions)
- **Website:** [https://azorian.solutions](https://azorian.solutions)

## TL;DR

    docker run -d -p 8080:80 -e PDAC_SIGNUP_ENABLED=true ngoduykhanh/powerdns-nameserver

## [Azorian Solutions](https://azorian.solutions) Docker image strategy

The goal of creating this image and others alike is to provide a fairly uniform and turn-key implementation for a chosen set of products and solutions. By compiling the server binaries from source code, a greater chain of security is maintained by eliminating unnecessary trusts. This approach also helps assure support of specific features that may otherwise vary from distribution to distribution. A secondary goal of creating this image and others alike is to provide at least two Linux distribution options for any supported product or solution which is why you will often see tags for both Alpine Linux and Debian Linux.

All documentation will be written with the assumption that you are already reasonably familiar with this ecosystem. This includes container concepts, the Docker ecosystem, and more specifically the product or solution that you are deploying. Simply put, I won't be fluffing the docs with content explaining every detail of what is presented.

## Supported tags

\* denotes an image that is planned but has not yet been released.

### Alpine Linux

- main, latest
- 0.2.4-alpine, alpine, 0.2.4

### Debian Linux

- 0.2.4-debian, debian

## Deploying this image

### App configuration

Configuration of the PowerDNS Admin app may be achieved through a mixture of two approaches. With either approach you choose, you will need to be aware of the various settings available for the app.

[PowerDNS Admin Settings](https://github.com/ngoduykhanh/PowerDNS-Admin/blob/master/docs/settings.md)

#### Approach #1

You may pass app settings as environment variables to the container. These environment variables will be automatically inserted into the app.config object. Any environment variable that begins with PDA_ or PDAC_ and is entirely capitalized, will be inserted into the app.config object.

**One key difference** between the two variable prefixes is that variables prefixed with PDAC_ will have the PDAC_ prefix removed before being inserted into the app.config object.

For example, say you pass the environment variable PDA_BIND_ADDRESS with the value 0.0.0.0 to the container. 

    PDA_BIND_ADDRESS=0.0.0.0

This will create a key named PDA_BIND_ADDRESS in app.config with the value of the environment variable value of 0.0.0.0.

Similar to how secrets work for Docker Swarm containers, you may append _FILE to your environment variables to automatically load the contents of the given file path into an environment variable.

**One key difference** here from Docker Swarm secrets is that you provide an absolute file path to any path of our choosing. Also, once the contents of the file are loaded, an environment variable of the same name without the trailing _FILE is created with the contents of the loaded file as the value. The original environment variable with the trailing _FILE is removed.

The following example illustrates a scenario where you want to set the PDA_PDNS_API_KEY app setting in a secure fashion. You have the secret API key stored at /run/secrets/PDA_PDNS_API_KEY.

    PDA_PDNS_API_KEY_FILE=/run/secrets/PDA_PDNS_API_KEY

This would be the equivalent of running:

    export PDA_PDNS_API_KEY=CONTENTS_OF_SECRET_FILE

#### Approach #2

With this approach, you may create traditional PowerDNS Admin config files and map them to an accessible location inside the container. Then you can pass an environment variable to indicate where to load the file from.

For example, say you have mapped a python configuration file to /srv/app/configs/my-config.py in the container. You would add the following environment variable to your deployment configuration:

    FLASK_CONF=/srv/app/configs/my-config.py

**!!! NOTICE !!!** - There is a very specific order in which different sources are loaded. Take careful notice to avoid confusion!

- The config file **/srv/app/configs/default.py** is loaded.
- The **FLASK_CONF** environment variable is loaded if configured.
- Any instance specific configuration provided via code instantiation is loaded.
- Settings are loaded individually from any environment variables present.
- If all required MySQL settings are present in the app.config object and no SQLALCHEMY_DATABASE_URI app setting has been configured, the app.config setting will be automatically created from the provided MySQL settings.
  - Otherwise, the SQLALCHEMY_DATABASE_URI app setting is set to "sqlite:////srv/app/pdns.db"

### Deploy with Docker Run

To run a simple container on Docker with this image, execute the following Docker command;

    docker run -d -p 8080:80 -e PDAC_SIGNUP_ENABLED=true ngoduykhanh/powerdns-nameserver

### Deploy with Docker Compose

To run this image using Docker Compose, create a YAML file in a place of your choosing and add the following contents to it;

    version: "3.3"
    services:
      powerdns-admin:
        image: ngoduykhanh/powerdns-admin
        restart: unless-stopped
        environment:
          - PDAC_SALT=ntR8BmMQb7MKTJ5YrgQwZr3pxU3uLG
          - PDAC_SECRET_KEY=eJ92QLuennVStHTj5FVwxz7m4r3Ng3
        ports:
          - "8080:80"

Then execute the following Docker Compose command;

    docker-compose -f /path/to/yaml/file.yml up

**!!! NOTICE !!!** - Make sure to set the environment variable `PDAC_SECRET_KEY` to a long random string ([see here for additional information](https://flask.palletsprojects.com/en/1.1.x/config/#SECRET_KEY))

## Building this image

If you want to build this image yourself, you can easily do so using the **docker/bin/build-image** command I have included.

The build-image command has the following parameter format;

    build-image IMAGE_TAG_NAME APP_VERSION DISTRO_NAME DISTRO_TAG

So for example, to build the PowerDNS Admin app version 0.2.3 on Alpine Linux 3.14, you would execute the following shell command:

    build-image 0.2.3-alpine-3.14 0.2.3 alpine 3.14

The build-image command assumes the following parameter defaults;

- Image Tag Name: latest
- App Version: 0.2.4
- Distro Name: alpine
- Distro Tag: 3.14

This means that running the build-image command with no parameters would be the equivalent of executing the following shell command:

    build-image latest 0.2.4 alpine 3.14

When the image is tagged during compilation, the repository portion of the image tag is derived from the contents of the docker/repo.cfg file and the tag from the first parameter provided to the build-image command.

