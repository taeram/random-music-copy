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
        Modified for use in random-copy.py by Jesse Patching
    """
    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(path), None, None, ctypes.pointer(free_bytes))
        free_space = free_bytes.value
    else:
        st = os.statvfs(path)
        free_space = st.f_bavail * st.f_frsize

    return free_space

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
        for filename in filenames:
            if filename.endswith('mp3'):
                filepath = os.path.join(dirname, filename)
                found_files.append(filepath)

    if not found_files:
        error('No files found, exiting...')

    # Randomize the list of files
    shuffle(found_files)

    if args.file_count is None:
        # Copy all the files!
        args.file_count = len(found_files)

    copied_count = 0
    copied_size = 0
    print 'Copying files...'
    for file in found_files:
        # Update the size of the copied files
        file_size = os.stat(file).st_size
        if (copied_size + file_size) > args.max_size:
            print "Destination full!"
            break
        copied_size += file_size

        # Test the file count limit
        if (copied_count + 1) > args.file_count:
            print "File limit reached!"
            break
        copied_count += 1

        # Copy the file, ensuring there aren't any duplicates
        print "    - %s" % file
        file_dest = "%s%04d - %s" % (args.dest_dir, copied_count, os.path.basename(file))
        copyfile(file, file_dest)

    print 'Done! Copied %s files totalling %s MB ' % (copied_count, (copied_size/1024*1024))
    exit(0)

if __name__ == '__main__':
    main()
