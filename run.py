#!/usr/bin/env python3
from powerdnsadmin import create_app

if __name__ == '__main__':
    app = create_app()
    # TODO: Update the following to source the debug mode setting from either the application configuration or the
    # environment variable FLASK_DEBUG. I believe support for the environment variable is already built-in to Flask
    # so perhaps this just needs to negate the use of the debug flag if the environment variable is present
    app.run(debug=app.config.get('DEBUG_MODE', False), host=app.config.get('BIND_ADDRESS', '0.0.0.0'),
            port=app.config.get('PORT', '80'))
