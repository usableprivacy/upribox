import zipfile
from datetime import datetime
from lib.utils import get_default, call_ansible
from os.path import isdir, join, abspath
import os
import stat
import struct

# specify full paths
BACKUP_LOCATIONS = [
    "/etc/ansible/facts.d",
    get_default("django", "db"),
    get_default("log", "general", "path"),
    "/etc/openvpn/ca"
]

BACKUP_NAME = "upri_backup_{}.zip"

# ID + LENGTH in bytes
EXTRA_HEADER_LENGTH = 4
# extra field that stores UNIX UID/GID data
EXTRA_ID = 0x7875
# length of the following data (after the id and the length)
EXTRA_LENGTH = 11
EXTRA_VERSION = 0x1
# system zip utility stores uid/gid using 4 bytes
EXTRA_UID_SIZE = 4
EXTRA_GID_SIZE = 4
# little endian: id, length, version, uid_size, uid, gid_size, gid
EXTRA_FORMAT = "<HHBBLBL"

# unix permissions in high order bytes
UNIX_PERM_BYTES = 16L


def action_backup(arg):
    timestamp = datetime.now()
    try:
        zpath = join(abspath(arg), BACKUP_NAME.format(timestamp))
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for location in BACKUP_LOCATIONS:

                if isdir(location):
                    # directory
                    zipdir(location, zipf)
                else:
                    # file
                    try:
                        write_file(zipf, location)
                    except ValueError as ve:
                        print ve
                        # try other files if one file fails
    except EnvironmentError:
        try:
            os.remove(BACKUP_NAME.format(timestamp))
        except Exception:
            pass
        print 'Unable to create backup archive'
        return 1


def action_restore(arg):
    stat_res = None
    zipf = None

    try:
        # try to open archive, don't follow symlinks
        stat_res = os.lstat(arg)
    except OSError as ose:
        print 'Unable to open archive'
        return 1

    if not (stat_res.st_uid == 0 and stat_res.st_gid == 0 and stat.S_ISREG(stat_res.st_mode) and not stat_res.st_mode & stat.S_IWOTH):
        # requirement: uid and gid == root, regular file (no link), not world-writeable (o-w)
        print 'file has unacceptable permissions'
        return 2

    try:
        with zipfile.ZipFile(arg, 'r', zipfile.ZIP_DEFLATED) as zipf:
            # for each file in archive
            for name in zipf.namelist():

                # check if file from archive is specified in BACKUP_LOCATIONS or is at least in one of the directories
                contained = False
                for entry in BACKUP_LOCATIONS:
                    if name.startswith(entry):
                        contained = True
                        break

                if not contained:
                    print 'omitting not permitted file %s' % (name,)
                else:
                    try:
                        extract_file(zipf, name)
                    except ValueError:
                        print "omitting file %s with incorrect or missing uid/gid extra field" % (name,)

        print 'files restored'
        print 'applying settings'
        # apply settings from restored local facts
        return call_ansible("all")
    except OSError as ose:
        print 'Unable to restore backup'
        print ose
        return 3


def extract_file(zipf, name):
    """Extracts one file from an archive and tries to restore file permissions and file uid/gid."""
    info = zipf.getinfo(name)

    # try to get date from the extra field that stores UNIX UID/GID data
    entry = get_entry(info.extra, EXTRA_ID, EXTRA_FORMAT)
    if not entry:
        raise ValueError()

    try:
        uid = entry[4]
        gid = entry[6]
    except IndexError:
        raise ValueError()

    # extract file with / as working dir, because archive contains absolute paths
    out_path = zipf.extract(name, "/")

    # external_attr is 4 bytes in size. The high order two
    # bytes represent UNIX permission and file type bits,
    # while the low order two contain MS-DOS FAT file
    # attributes, most notably bit 4 marking directories.
    perm = info.external_attr >> UNIX_PERM_BYTES
    # set file permissions
    os.chmod(out_path, perm)
    # set file uid/gid, don't follow symlinks
    os.lchown(out_path, uid, gid)


def write_file(zipf, name):
    """Writes one file into an archive and tries to preserve file permissions and file uid/gid."""
    # get time of last file modification
    try:
        timestamp = os.path.getmtime(name)
    except OSError:
        # print 'Unable to stat file %s' % (name,)
        raise ValueError('Unable to get modification time of file %s' % (name,))

    tinfo = datetime.fromtimestamp(timestamp)
    # prepare datetime for ZipInfo as tuple with 6 values
    date_tuple = (tinfo.year, tinfo.month, tinfo.day, tinfo.hour, tinfo.minute, tinfo.second)
    # create archive entry as ZipInfo, because storing extra information is not possible otherwise
    info = zipfile.ZipInfo(filename=name, date_time=date_tuple)
    # get uid/gid and file permissions
    try:
        # try to open archive, don't follow symlinks
        stat_res = os.lstat(name)
    except OSError:
        # print 'Unable to stat file %s' % (name,)
        raise ValueError('Unable to stat file %s' % (name,))
    # https://stackoverflow.com/questions/434641/how-do-i-set-permissions-attributes-on-a-file-in-a-zip-file-using-pythons-zip
    # external_attr is 4 bytes in size. The high order two
    # bytes represent UNIX permission and file type bits,
    # while the low order two contain MS-DOS FAT file
    # attributes, most notably bit 4 marking directories.
    info.external_attr = stat_res.st_mode << UNIX_PERM_BYTES
    uid = stat_res.st_uid
    gid = stat_res.st_gid
    # https://commons.apache.org/proper/commons-compress/apidocs/org/apache/commons/compress/archivers/zip/X7875_NewUnix.html
    # store extra filed as follows: little endian: id, length, version, uid_size, uid, gid_size, gid
    info.extra = struct.pack(EXTRA_FORMAT, EXTRA_ID, EXTRA_LENGTH, EXTRA_VERSION, EXTRA_UID_SIZE, uid, EXTRA_GID_SIZE, gid)
    # write entry info and data into zipfile
    try:
        with open(name) as data:
            zipf.writestr(info, data.read(), zipfile.ZIP_DEFLATED)
    except (IOError, RuntimeError, OSError):
        # print 'unable to write data from file %s to archive' % (name,)
        raise ValueError('unable to write data from file %s to archive' % (name,))


def get_entry(extra, id, format):
    """Searches for a specific extra field inside the extra value of the ZipInfo."""
    # make bytesequence mutable
    array = bytearray(extra)
    try:
        # while extra value is not empty
        while len(array) > 0:
            # extract first extra field id and length
            entry_id, length = struct.unpack("<HH" + "x" * (len(array) - EXTRA_HEADER_LENGTH), array)
            # if desired extra field has not been found
            if entry_id != id:
                # remove the extra field bytes from the bytearray
                del array[:length + EXTRA_HEADER_LENGTH]
            else:
                # unpack and return values of desired extra field
                return struct.unpack(format, array)
    except struct.error:
        return None


def zipdir(path, zipf):
    """Walks a directory and writes all files in an archive."""
    for root, dirs, files in os.walk(path):
        for file in files:
            # write_file(ziph, join(root, file), join(dest, relpath(join(root, file), path)))
            try:
                write_file(zipf, join(root, file))
            except ValueError as ve:
                print ve
                # try other files if one file fails
