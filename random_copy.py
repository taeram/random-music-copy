#!/usr/bin/env python
# -*- coding: utf8 -*-

import ctypes
from argparse import ArgumentParser
import os
import platform
from shutil import copyfile
from random import shuffle
from sys import exit

def get_free_disk_space(path):
    """
        Return free space in bytes for a path

        Retrieved on 2014-10-09 from https://stackoverflow.com/a/2372171/27810
        Modified for use in random-copy-music by Jesse Patching
    """
    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(path), None, None, ctypes.pointer(free_bytes))
        free_space = free_bytes.value
    else:
        st = os.statvfs(path)
        free_space = st.f_bavail * st.f_frsize

    return free_space


def touch(fname, times=None):
    """
        Touch a file, setting it's modification time

        Retrieved on 2014-10-09 from https://stackoverflow.com/a/1160227/27810
        Modified for use in random-copy-music by Jesse Patching
    """
    fhandle = open(fname, 'a')
    try:
        os.utime(fname, times)
    finally:
        fhandle.close()

def error(message):
    print '\033[91m' + message + '\033[0m'
    exit(1)

def main():

    # Setup the parser options
    parser = ArgumentParser(description="Copy a bunch of random MP3's from your library")
    parser.add_argument('source_dir', metavar='source_dir', help='The location of your MP3 library')
    parser.add_argument('dest_dir', metavar='dest_dir', help="Where to copy the random MP3's to")
    parser.add_argument('-s', '--size', dest='max_size', action='store', type=int, default=None, help='Total size of copied files, in megabytes')
    parser.add_argument('-n', '--number-of-files', dest='file_count', action='store', type=int, default=None, help='Maximum number of files to copy')
    parser.add_argument('-f', '--use-folders', dest='use_folders', action='store_true', help="Put the files in folders to support stereos with file limits")
    parser.add_argument('-l', '--folder-file-limit', dest='folder_file_count', action='store', type=int, default=20, help="The number of files to store in each folder")
    parser.add_argument('-e', '--exclude', dest='excludes', action='store', nargs="*", help="A list of files/dirs to exclude")
    parser.add_argument('-d', '--dry-run', dest='dry_run', action='store_true', help="Just perform a dry run")
    args = parser.parse_args()

    # Does the source directory exist?
    if not os.path.isdir(args.source_dir):
        error('No such directory: ' + args.source_dir)

    # Does the destination directory exist?
    if not os.path.isdir(args.dest_dir):
        error('No such directory: ' + args.dest_dir)

    # If no size limit specified, fill the destination
    if args.max_size is None:
        args.max_size = get_free_disk_space(args.dest_dir)
    else:
        # Convert megabytes to bytes
        args.max_size = args.max_size * 1024 * 1024

        # Ensure there's enough free space
        if get_free_disk_space(args.dest_dir) < args.max_size:
            error('Not enough free space in destination directory')

    # Get a list of files to copy
    print 'Scanning %s...' % args.source_dir
    found_files = []
    for dirname, dirnames, filenames in os.walk(args.source_dir, followlinks=True):
        skip_dir = False
        for exclude in args.excludes:
            if exclude.lower() in dirname.lower():
                skip_dir = True
                break

        if not skip_dir:
            for filename in filenames:
                skip_file = False
                for exclude in args.excludes:
                    if exclude.lower() in filename.lower():
                        skip_file = True
                        break

                if not skip_file and filename.endswith('mp3'):
                    filepath = os.path.join(dirname, filename)
                    found_files.append(filepath)

    if not found_files:
        error('No files found, exiting...')

    # Randomize the list of files
    shuffle(found_files)

    if args.file_count is None:
        # Copy all the files!
        args.file_count = len(found_files)

    folder_count = 0
    copied_count = 0
    copied_size = 0
    print 'Copying files...'
    for file in found_files:
        # Update the size of the copied files
        file_size = os.stat(file).st_size
        if (copied_size + file_size) > args.max_size:
            print "Destination full!"
            break

        # Test the file count limit
        if (copied_count + 1) > args.file_count:
            print "File limit reached!"
            break

        print "    - %s" % file

        # What folder do we store this file in
        file_dir = args.dest_dir
        if args.use_folders:
            if copied_count / args.folder_file_count > folder_count:
                folder_count += 1

            file_dir = "%s/%04d" % (file_dir, folder_count)

            if not args.dry_run and not os.path.exists(file_dir):
                os.makedirs(file_dir)

        # Give the file a unique prefix, ensuring we won't overwrite any existing files
        file_name = "%04d - %s" % (copied_count, os.path.basename(file))

        file_dest = "%s/%s" % (file_dir, file_name)
        if not args.dry_run:
            copyfile(file, file_dest)

            # Since some stereos look at the modification time to determine file sorting,
            # touch the file after it's been copied to set it's modification time to now
            touch(file_dest)

        # Update the counters
        copied_size += file_size
        copied_count += 1

    print 'Done! Copied %s files totalling %s MB ' % (copied_count, (copied_size/1024/1024))
    exit(0)

if __name__ == '__main__':
    main()
