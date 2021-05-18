#!/usr/bin/python3
import sys
import pymongo
from bson import json_util
import argparse


def log(verbose, *args):
    if verbose:
        print(*args)


def mongo_import(client: pymongo.MongoClient, fname: str, del_db: bool = False, del_col: bool = False, databases=None,
                 verbose=False, force=False):
    """

    :param client:
    :param fname:
    :param del_db:
    :param del_col:
    :return:
    """
    with open(fname, 'r') as input_conf:
        conf = json_util.loads(input_conf.read())
        for dbname, d in conf['databases'].items():
            if databases is not None and databases != "*" and dbname not in databases.split(','):
                log(verbose, "Skipping:", dbname)
                continue
            if del_db:
                log(verbose, "Dropping database:", dbname)
                client.drop_database(dbname)
            log(verbose, "Begin with database:", dbname)
            db = client[dbname]
            for cname, c in d.items():
                log(verbose, "\tBegin with collection:", cname)
                exists = False
                if dbname in ['config','admin', 'local']:
                    continue
                if del_col:
                    log(verbose, "\t\tDropping collection")
                    db.drop_collection(cname)
                else:
                    # if the collection already exists, skip it
                    if cname in db.list_collection_names():
                        print("\t\tAlready exists")
                        exists = True
                if not exists:
                    log(verbose, "\t\tCreating collection:")
                    log(verbose, "\t\t\tOptions", c['options'])
                    collection = db.create_collection(cname, **c['options'])
                else:
                    collection = db[cname]
                    indexes = [dict(x) for x in collection.list_indexes()]
                    name_indexes = []
                    for i in indexes:
                        name_indexes.append(i['name'])

                log(verbose, "\t\tCreate indexes")
                for i in c['indexes']:
                    if i['name'] in name_indexes:
                        log(verbose, "\t\t\tAlready existant index name:", i)
                        if not force:
                            continue

                    log(verbose, "\t\t\tCreating index:", i)
                    keys = [tuple(x) for x in i['keys']]
                    del i['keys']
                    try:
                        collection.create_index(keys, **i)
                    except pymongo.errors.OperationFailure as e:
                        log(verbose, "\t\tDropping index:",i['name'])
                        collection.drop_index(i['name'])
                        collection.create_index(keys, **i)

def main(argv=sys.argv):
    parser = argparse.ArgumentParser(description="Import a schema for database")
    parser.add_argument('--uri', metavar='uri', type=str,
                        help='Full uri, use in place of server/port/user/auth_db, eg: mongodb://user:pass@example.com:port/auth_db')
    parser.add_argument("--host", metavar='h', type=str, help='Server host', default='localhost')
    parser.add_argument("--port", metavar='p', type=int, help='Server port', default=27017)
    parser.add_argument('--username', metavar='u', type=str, help='Username', default='')
    parser.add_argument('--password', metavar='pwd', type=str, help='Username', default='')
    parser.add_argument('--authSource', metavar='a', type=str, help='DB to auth against', default='admin')
    parser.add_argument('--file', metavar='f', type=str, help='Path to exported .json file', default='config.json')
    parser.add_argument('--delete-db', action='store_true', help='Delete existing database if it exist')
    parser.add_argument('--delete-col', action='store_true',
                        help='Delete existing collections if they exist')
    parser.add_argument('--verbose', action='store_true', help='Display verbose output')
    parser.add_argument('--databases', metavar='db', type=str,
                        help='Select databases from the config json to insert, default is all of them', default='*')
    parser.add_argument('--force', metavar='F', type=str, help='Force the creation of the index')

    args = parser.parse_args(argv[1:])
    if args.uri:
        _client = pymongo.MongoClient(args.uri)
    else:
        client_args = {}
        for i in 'host', 'port', 'username', 'password', 'authSource':
            if hasattr(args, i):
                client_args[i] = getattr(args, i)
        _client = pymongo.MongoClient(**client_args)
    mongo_import(_client, args.file, args.delete_db, args.delete_col, args.databases, args.verbose, args.force)


if __name__ == "__main__":
    sys.exit(main() or 0)
