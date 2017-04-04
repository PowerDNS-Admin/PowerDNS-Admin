#!/usr/bin/env python
from powerDNSAdmin import app


if __name__ == '__main__':
    app.run(debug =True,
            host=app.config.get('BIND_ADDRESS',
                                '127.0.0.1'),
            port=app.config['PORT'])
