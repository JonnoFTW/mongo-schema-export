#!/usr/bin/env python
import sys
from collections import defaultdict
from datetime import datetime

import pymongo
from bson import json_util
import argparse


def log(verbose, *args):
    if verbose:
        print(*args)


def toInt(x):
    try:
        return int(x)
    except ValueError:
        return x


def mongo_export(client: pymongo.MongoClient, fname: str, databases: str, verbose: bool):
    """

    :param client:
    :param fname:
    :return:
    """
    out = defaultdict(dict)
    for dbname in databases.split(','):
        log(verbose, "Exporting database:", dbname)
        db = client[dbname]
        for cname in db.list_collection_names():
            coll = db[cname]
            log(verbose, "\tExporting collection", cname)
            opts = coll.options()
            autoIndexId = 'autoIndexId'
            if autoIndexId in opts:
                del opts[autoIndexId]  # this is deprecated
            indexes = [dict(x) for x in coll.list_indexes()]
            out_indexes = []
            for i in indexes:
                i['keys'] = [[k, toInt(v)] for k, v in i['key'].items()]
                for f in 'key', 'ns', 'v':
                    if f in i:
                        del i[f]
                out_indexes.append(i)

            out[dbname][cname] = {
                'indexes': out_indexes,
                'options': opts
            }
    with open(fname, 'w') as out_file:
        out_str = json_util.dumps({
            'databases': out,
            'exported': datetime.now().isoformat()
        }, indent=4)
        out_file.write(out_str)
    return out_str


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(description="Export a schema for a mongodb database")
    parser.add_argument('--uri', metavar='uri', type=str,
                        help='Full uri, use in place of server/port/user/auth_db, eg: mongodb://user:pass@example.com:port/auth_db')
    parser.add_argument("--host", metavar='h', type=str, help='Server host', default='localhost')
    parser.add_argument("--port", metavar='p', type=int, help='Server port', default=27017)
    parser.add_argument('--username', metavar='u', type=str, help='Username', default='')
    parser.add_argument('--password', metavar='pwd', type=str, help='Password', default='')
    parser.add_argument('--authSource', metavar='a', type=str, help='DB to auth against', default='admin')
    parser.add_argument('--file', metavar='f', type=str, help='Path to exported .json file', default='config.json')
    parser.add_argument('--databases', metavar='db', type=str,
                        help='Databases separated by a comma, eg: db_1,db_2,db_n')
    parser.add_argument('--verbose', action='store_true', help='Show verbose output')
    args = parser.parse_args(argv[1:])
    if not args.databases:
        exit("Please specify at least one database to export")
    if args.uri:
        _client = pymongo.MongoClient(args.uri)
    else:
        client_args = {}
        for i in 'host', 'port', 'username', 'password', 'authSource':
            if hasattr(args, i):
                client_args[i] = getattr(args, i)
        _client = pymongo.MongoClient(**client_args)

    s = mongo_export(_client, args.file, args.databases, args.verbose)
    if args.verbose:
        print(s)


if __name__ == "__main__":
    sys.exit(main() or 0)
