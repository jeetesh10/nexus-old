#!/usr/bin/env python3
"""
Seed the MongoDB ui_tabs collection for Nexus Admin/Landing.

Usage:
  MONGODB_URI='mongodb://mongodb-service:27017' python scripts/seed-ui-tabs.py \
    --db nexus --collection ui_tabs --file config/ui_tabs.seed.json

Env vars (with defaults):
  - MONGODB_URI: Mongo connection string (default: mongodb://localhost:27017)
  - MONGODB_DB:  Database name (default: nexus)
  - MONGODB_COLLECTION: Collection name (default: ui_tabs)

The seed JSON is an array of documents. Existing docs with the same `id` will be
upserted; others will be inserted. Documents missing `id` are skipped.
"""
import argparse
import json
import os
from typing import Any, Dict, List

from pymongo import MongoClient


def load_seed(path: str) -> List[Dict[str, Any]]:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and 'tabs' in data and isinstance(data['tabs'], list):
            return data['tabs']
        raise ValueError('Seed file must be a JSON array or an object with a "tabs" array')


def main():
    parser = argparse.ArgumentParser(description='Seed ui_tabs collection')
    parser.add_argument('--uri', default=os.getenv('MONGODB_URI', 'mongodb://localhost:27017'))
    parser.add_argument('--db', default=os.getenv('MONGODB_DB', 'nexus'))
    parser.add_argument('--collection', default=os.getenv('MONGODB_COLLECTION', 'ui_tabs'))
    parser.add_argument('--file', default=os.getenv('UI_TABS_SEED', 'config/ui_tabs.seed.json'))
    args = parser.parse_args()

    seed = load_seed(args.file)
    client = MongoClient(args.uri)
    coll = client[args.db][args.collection]

    upserts = 0
    inserts = 0
    for doc in seed:
        if not isinstance(doc, dict):
            continue
        _id = doc.get('id')
        if not _id:
            continue
        res = coll.update_one({'id': _id}, {'$set': doc}, upsert=True)
        if res.matched_count:
            upserts += 1
        elif res.upserted_id is not None:
            inserts += 1
    print(f"Seed complete. Upserts: {upserts}, Inserts: {inserts}, Total processed: {len(seed)}")


if __name__ == '__main__':
    main()
