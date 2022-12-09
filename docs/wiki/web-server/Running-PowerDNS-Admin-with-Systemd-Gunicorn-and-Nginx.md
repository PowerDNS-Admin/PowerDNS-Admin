Following is an example showing how to run PowerDNS-Admin with systemd, gunicorn and nginx:

## Configure PowerDNS-Admin

Create PowerDNS-Admin config file and make the changes necessary for your use case. Make sure to change `SECRET_KEY` to a long random string that you generated yourself ([see Flask docs](https://flask.palletsprojects.com/en/1.1.x/config/#SECRET_KEY)), do not use the pre-defined one.
```
$ cp /opt/web/powerdns-admin/configs/development.py /opt/web/powerdns-admin/configs/production.py
$ vim /opt/web/powerdns-admin/configs/production.py
```

## Configure systemd service

`$ sudo vim /etc/systemd/system/powerdns-admin.service`

```
[Unit]
Description=PowerDNS-Admin
Requires=powerdns-admin.socket
After=network.target

[Service]
PIDFile=/run/powerdns-admin/pid
User=pdns
Group=pdns
WorkingDirectory=/opt/web/powerdns-admin
ExecStartPre=+mkdir -p /run/powerdns-admin/
ExecStartPre=+chown pdns:pdns -R /run/powerdns-admin/
ExecStart=/usr/local/bin/gunicorn --pid /run/powerdns-admin/pid --bind unix:/run/powerdns-admin/socket 'powerdnsadmin:create_app()'
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

`$ sudo systemctl edit powerdns-admin.service`

```
[Service]
Environment="FLASK_CONF=../configs/production.py"
```

`$ sudo vim /etc/systemd/system/powerdns-admin.socket`

```
[Unit]
Description=PowerDNS-Admin socket

[Socket]
ListenStream=/run/powerdns-admin/socket

[Install]
WantedBy=sockets.target
```

`$ sudo vim /etc/tmpfiles.d/powerdns-admin.conf`

```
d /run/powerdns-admin 0755 pdns pdns -
```

Then `sudo systemctl daemon-reload; sudo systemctl start powerdns-admin.socket; sudo systemctl enable powerdns-admin.socket` to start the Powerdns-Admin service and make it run on boot.

## Sample nginx configuration
```
server {
  listen *:80;
  server_name               powerdns-admin.local www.powerdns-admin.local;

  index                     index.html index.htm index.php;
  root                      /opt/web/powerdns-admin;
  access_log                /var/log/nginx/powerdns-admin.local.access.log combined;
  error_log                 /var/log/nginx/powerdns-admin.local.error.log;

  client_max_body_size              10m;
  client_body_buffer_size           128k;
  proxy_redirect                    off;
  proxy_connect_timeout             90;
  proxy_send_timeout                90;
  proxy_read_timeout                90;
  proxy_buffers                     32 4k;
  proxy_buffer_size                 8k;
  proxy_set_header                  Host $host;
  proxy_set_header                  X-Real-IP $remote_addr;
  proxy_set_header                  X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_headers_hash_bucket_size    64;

  location ~ ^/static/  {
    include  /etc/nginx/mime.types;
    root /opt/web/powerdns-admin/powerdnsadmin;

    location ~*  \.(jpg|jpeg|png|gif)$ {
      expires 365d;
    }

    location ~* ^.+.(css|js)$ {
      expires 7d;
    }
  }

  location / {
    proxy_pass            http://unix:/run/powerdns-admin/socket;
    proxy_read_timeout    120;
    proxy_connect_timeout 120;
    proxy_redirect        off;
  }

}
```

<details>
<summary>Sample Nginx-Configuration for SSL</summary>

* Im binding this config to every dns-name with default_server...
* but you can remove it and set your server_name.

```
server {
        listen                  80 default_server;
        server_name             "";
        return 301 https://$http_host$request_uri;
}

server {
        listen                  443 ssl http2 default_server;
        server_name             _;
        index                   index.html index.htm;
        error_log               /var/log/nginx/error_powerdnsadmin.log error;
        access_log              off;

        ssl_certificate                 path_to_your_fullchain_or_cert;
        ssl_certificate_key             path_to_your_key;
        ssl_dhparam                     path_to_your_dhparam.pem;
        ssl_prefer_server_ciphers       on;
        ssl_ciphers                     'EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH';
        ssl_session_cache               shared:SSL:10m;

        client_max_body_size            10m;
        client_body_buffer_size         128k;
        proxy_redirect                  off;
        proxy_connect_timeout           90;
        proxy_send_timeout              90;
        proxy_read_timeout              90;
        proxy_buffers                   32 4k;
        proxy_buffer_size               8k;
        proxy_set_header                Host $http_host;
        proxy_set_header                X-Scheme $scheme;
        proxy_set_header                X-Real-IP $remote_addr;
        proxy_set_header                X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header                X-Forwarded-Proto $scheme;
        proxy_headers_hash_bucket_size  64;

        location ~ ^/static/  {
                include         mime.types;
                root            /opt/web/powerdns-admin/powerdnsadmin;
                location        ~* \.(jpg|jpeg|png|gif)$ { expires 365d; }
                location        ~* ^.+.(css|js)$ { expires 7d; }
        }

        location ~ ^/upload/  {
                include         mime.types;
                root            /opt/web/powerdns-admin;
                location        ~* \.(jpg|jpeg|png|gif)$ { expires 365d; }
                location        ~* ^.+.(css|js)$ { expires 7d; }
        }

        location / {
                proxy_pass              http://unix:/run/powerdns-admin/socket;
                proxy_read_timeout      120;
                proxy_connect_timeout   120;
                proxy_redirect          http:// $scheme://;
        }
}
```
</details>

## Note
* `/opt/web/powerdns-admin` is the path to your powerdns-admin web directory
* Make sure you have installed gunicorn in flask virtualenv already.
* `powerdns-admin.local` just an example of your web domain name.