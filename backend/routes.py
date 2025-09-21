from . import app
import os
import json
import pymongo
from flask import jsonify, request
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from bson.objectid import ObjectId
from http import HTTPStatus
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# Mongo connection from environment variables
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service is None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"

print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)


def parse_json(data):
    return json.loads(json_util.dumps(data))


######################################################################
# Exercise 1: Health and Count
######################################################################

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "OK"}), HTTPStatus.OK


@app.route("/count", methods=["GET"])
def count():
    """Count songs in the collection"""
    count = db.songs.count_documents({})
    return jsonify({"count": count}), HTTPStatus.OK


######################################################################
# Exercise 2: GET /song (list all)
######################################################################

@app.route("/song", methods=["GET"])
def get_songs():
    songs = list(db.songs.find({}))
    return json_util.dumps({"songs": songs}), HTTPStatus.OK


######################################################################
# Exercise 3: GET /song/<id>
######################################################################

@app.route("/song/<int:song_id>", methods=["GET"])
def get_song(song_id):
    song = db.songs.find_one({"id": song_id})
    if not song:
        return jsonify({"message": "song with id not found"}), HTTPStatus.NOT_FOUND
    return json_util.dumps(song), HTTPStatus.OK


######################################################################
# Exercise 4: POST /song
######################################################################

@app.route("/song", methods=["POST"])
def create_song():
    song = request.get_json()

    if db.songs.find_one({"id": song["id"]}):
        return jsonify({"Message": f"song with id {song['id']} already present"}), HTTPStatus.FOUND

    result = db.songs.insert_one(song)
    return jsonify({"inserted id": str(result.inserted_id)}), HTTPStatus.CREATED


######################################################################
# Exercise 5: PUT /song/<id>
######################################################################

@app.route("/song/<int:song_id>", methods=["PUT"])
def update_song(song_id):
    song_data = request.get_json()
    existing_song = db.songs.find_one({"id": song_id})

    if not existing_song:
        return jsonify({"message": "song not found"}), HTTPStatus.NOT_FOUND

    result = db.songs.update_one({"id": song_id}, {"$set": song_data})

    if result.modified_count == 0:
        return jsonify({"message": "song found, but nothing updated"}), HTTPStatus.OK

    updated_song = db.songs.find_one({"id": song_id})
    return json_util.dumps(updated_song), HTTPStatus.CREATED


######################################################################
# Exercise 6: DELETE /song/<id>
######################################################################

@app.route("/song/<int:song_id>", methods=["DELETE"])
def delete_song(song_id):
    result = db.songs.delete_one({"id": song_id})
    if result.deleted_count == 0:
        return jsonify({"message": "song not found"}), HTTPStatus.NOT_FOUND
    return "", HTTPStatus.NO_CONTENT
