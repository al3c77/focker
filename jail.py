import subprocess
from .zfs import *
import random
import shutil
import json
from tabulate import tabulate


def get_jid(path):
    data = json.loads(subprocess.check_output(['jls', '--libxo=json']))
    lst = data['jail-information']['jail']
    lst = list(filter(lambda a: a['path'] == path, lst))
    if len(lst) == 0:
        raise ValueError('JID not found for path: ' + path)
    if len(lst) > 1:
        raise ValueError('Ambiguous JID for path: ' + path)
    return str(lst[0]['jid'])


def do_mounts(path, mounts):
    print('mounts:', mounts)
    for (source, target) in mounts:
        if source.startswith('/'):
            name = source
        else:
            name, _ = zfs_find(source, focker_type='volume')
            name = zfs_mountpoint(name)
        while target.startswith('/'):
            target = target[1:]
        subprocess.check_output(['mount', '-t', 'nullfs', name, os.path.join(path, target)])


def undo_mounts(path, mounts):
    for (_, target) in reversed(mounts):
        while target.startswith('/'):
            target = target[1:]
        subprocess.check_output(['umount', '-f', os.path.join(path, target)])


def jail_run(path, command, mounts=[]):
    command = ['jail', '-c', 'host.hostname=' + os.path.split(path)[1], 'persist=1', 'mount.devfs=1', 'interface=lo1', 'ip4.addr=127.0.1.0', 'path=' + path, 'command', '/bin/sh', '-c', command]
    print('Running:', ' '.join(command))
    try:
        do_mounts(path, mounts)
        shutil.copyfile('/etc/resolv.conf', os.path.join(path, 'etc/resolv.conf'))
        res = subprocess.run(command)
    finally:
        try:
            subprocess.run(['jail', '-r', get_jid(path)])
        except ValueError:
            pass
        subprocess.run(['umount', '-f', os.path.join(path, 'dev')])
        undo_mounts(path, mounts)
    if res.returncode != 0:
        # subprocess.run(['umount', os.path.join(path, 'dev')])
        raise RuntimeError('Command failed')


def command_jail_run(args):
    base, _ = zfs_snapshot_by_tag_or_sha256(args.image)
    # root = '/'.join(base.split('/')[:-1])
    for _ in range(10**6):
        sha256 = bytes([ random.randint(0, 255) for _ in range(32) ]).hex()
        name = sha256[:7]
        name = base.split('/')[0] + '/focker/jails/' + name
        if not zfs_exists(name):
            break
    zfs_run(['zfs', 'clone', '-o', 'focker:sha256=' + sha256, base, name])
    try:
        mounts = list(map(lambda a: a.split(':'), args.mounts))
        jail_run(zfs_mountpoint(name), args.command, mounts)
        # subprocess.check_output(['jail', '-c', 'interface=lo1', 'ip4.addr=127.0.1.0', 'path=' + zfs_mountpoint(name), 'command', command])
    finally:
        # subprocess.run(['umount', zfs_mountpoint(name) + '/dev'])
        zfs_run(['zfs', 'destroy', '-f', name])
        # raise

def command_jail_list(args):
    lst = zfs_list(fields=['focker:sha256,focker:tags,mountpoint'], focker_type='jail')
    jails = subprocess.check_output(['jls', '--libxo=json'])
    jails = json.loads(jails)['jail-information']['jail']
    jails = { j['path']: j for j in jails }
    lst = list(map(lambda a: [ a[1],
        a[0] if args.full_sha256 else a[0][:7],
        a[2],
        jails[a[2]]['jid'] if a[2] in jails else '-' ], lst))
    print(tabulate(lst, headers=['Tags', 'SHA256', 'mountpoint', 'JID']))


def command_jail_tag(args):
    name, _ = zfs_find(args.reference, focker_type='jail')
    zfs_untag(args.tags, focker_type='jail')
    zfs_tag(name, args.tags)


def command_jail_untag(args):
    zfs_untag(args.tags, focker_type='jail')
