#!/usr/bin/env python
from get_mongo_client import get_mongo_client
cli = get_mongo_client()
db = cli.kinpri_theater_checker
db.drop_collection('shows_latest')

