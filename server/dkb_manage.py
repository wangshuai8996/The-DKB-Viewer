#!/usr/bin/env python3
# -*- coding:utf-8 -*-

'''
The admin management tool for DKB.
Things like initialising DKB are put here.
'''

import argparse
import os
from pathlib import Path

from dare_kb.server import setting
from dare_kb.common.Exceptions import DKBnotResetError, DKBnotFoundError
from dare_kb.server.DareKB import DareKB


def new_dkb(site_name: str, reset: bool = False) -> None:
    my_filename = setting.db_filename(site_name)
    if os.path.isfile(my_filename):
        if reset == True:
            os.remove(my_filename)
            print("You have erased a previous version of the DKB called "+site_name)
        else:
            raise DKBnotResetError(site_name)

    try:
        dkb = DareKB(setting.ontology_path, site_name)
    except Exception:
        raise DKBnotFoundError(site_name, "initDKB") from None


    ### From here all tests have been made, we can set the context and populate the DKB with the conceptual library

    ## Set the context to kb
    dkb._add_default_context()

    print('DKB "'+site_name+'" has been initialised ')

    dkb.shutdown()

def new_dkb(site_name: str, base_dir = '', reset = False, profile = None):
    my_filename = Path(base_dir) / setting.database_path
    if os.path.isfile(my_filename):
        if reset == True:
            os.remove(my_filename)
            print("You have erased a previous version of the DKB called "+site_name)
        else:
            raise DKBnotResetError(site_name)

    dkb = DareKB(site_name, base_dir=base_dir)

    ### From here all tests have been made, we can set the context and populate the DKB with the conceptual library

    ## Set the context to kb
    dkb._add_default_context()

    print('DKB "'+site_name+'" has been initialised ')

    # dkb.close()
    dkb.shutdown()


def delete(instanceName, base_dir=''):
    myfilename = Path(base_dir) / setting.database_path
    if os.path.isfile(myfilename):
        os.remove(myfilename)
    else:
        raise DKBnotFoundError(instanceName, 'delete')


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='sub-command',
            dest='command',
            help='The DKB management command to execute.')

    subparser = subparsers.add_parser('init',
            help='Initialise a new DKB (resetting an existing one optionally).')
    subparser.add_argument('site_name')
    subparser.add_argument('-d', '--directory', nargs='?', default='')
    subparser.add_argument('--reset',
            action='store_true')

    subparser = subparsers.add_parser('delete',
            help='Delete an existing DKB instance.')
    subparser.add_argument('site_name')
    subparser.add_argument('-d', '--directory', nargs='?', default='')

    args = parser.parse_args()

    if args.command == 'init':
        instanceName = args.site_name
        reset = args.reset
        base_dir = args.directory
        new_dkb(instanceName, base_dir=base_dir, reset=reset)
    elif args.command == 'delete':
        instanceName = args.site_name
        base_dir = args.directory
        delete(instanceName, base_dir=base_dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
