#!/usr/bin/env python3
from powerdnsadmin import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host=app.config.get('BIND_ADDRESS', app.config.get('PDA_BIND_ADDRESS', '0.0.0.0')),
        port=app.config.get('PORT', app.config.get('PDA_BIND_PORT', 80)),
        debug=app.config.get('DEBUG_MODE', app.config.get('PDA_DEBUG', False))
    )
