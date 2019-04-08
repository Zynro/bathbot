#!/bin/bash
python /srv/app/botr.py & cd images && python -m http.server $PORT
