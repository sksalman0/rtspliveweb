from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

overlay_bp = Blueprint("overlay_bp", __name__)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/overlay_db")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client.get_default_database()
overlays_col = db.get_collection("overlays")

# Utility to transform Mongo document to JSON serializable
def serialize(doc):
    doc["_id"] = str(doc["_id"])
    return doc

@overlay_bp.route("/overlays", methods=["GET"])
def list_overlays():
    docs = list(overlays_col.find({}))
    return jsonify([serialize(d) for d in docs]), 200

@overlay_bp.route("/overlays", methods=["POST"])
def create_overlay():
    data = request.get_json(force=True)
    # expected fields: type, content, x_pos, y_pos, width, height, color, font_size
    allowed = {"type","content","x_pos","y_pos","width","height","color","font_size"}
    doc = {k: data[k] for k in data if k in allowed}
    res = overlays_col.insert_one(doc)
    return jsonify({"id": str(res.inserted_id)}), 201

@overlay_bp.route("/overlays/<id>", methods=["PUT"])
def update_overlay(id):
    data = request.get_json(force=True)
    allowed = {"type","content","x_pos","y_pos","width","height","color","font_size"}
    update = {k: data[k] for k in data if k in allowed}
    if not update:
        return jsonify({"error":"no valid fields"}), 400
    res = overlays_col.update_one({"_id": ObjectId(id)}, {"$set": update})
    if res.matched_count == 0:
        return jsonify({"error":"not found"}), 404
    return jsonify({"ok":True}), 200

@overlay_bp.route("/overlays/<id>", methods=["DELETE"])
def delete_overlay(id):
    res = overlays_col.delete_one({"_id": ObjectId(id)})
    if res.deleted_count == 0:
        return jsonify({"error":"not found"}), 404
    return jsonify({"ok":True}), 200

@overlay_bp.route("/overlays/<id>", methods=["GET"])
def get_overlay(id):
    doc = overlays_col.find_one({"_id": ObjectId(id)})
    if not doc:
        return jsonify({"error":"not found"}), 404
    return jsonify(serialize(doc)), 200
