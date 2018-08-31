#!/usr/bin/env python3
from app import app
from config import PORT
from config import BIND_ADDRESS

if __name__ == '__main__':
    app.run(debug = True, host=BIND_ADDRESS, port=PORT)
