#!/usr/bin/env python3
from app import app
from config import PORT
from config import DEBUG_MODE

try:
	from config import BIND_ADDRESS
except:
	BIND_ADDRESS = '127.0.0.1'

if __name__ == '__main__':
    app.run(debug=DEBUG_MODE, host=BIND_ADDRESS, port=PORT)
