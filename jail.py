import subprocess
from .zfs import *
import random
import shutil


def jail_run(path, command):
    command = ['jail', '-c', 'host.hostname=' + os.path.split(path)[1], 'mount.devfs=1', 'interface=lo1', 'ip4.addr=127.0.1.0', 'path=' + path, 'command', '/bin/sh', '-c', command]
    print('Running:', ' '.join(command))
    res = subprocess.run(command)
    if res.returncode != 0:
        raise RuntimeError('Command failed')


def command_jail_run(args):
    base, _ = zfs_snapshot_by_tag_or_sha256(args.image)
    # root = '/'.join(base.split('/')[:-1])
    for _ in range(10**6):
        name = bytes([ random.randint(0, 256) for _ in range(4) ]).hex()[:7]
        name = base.split('/')[0] + '/focker/jails/' + name
        if not zfs_exists(name):
            break
    zfs_run(['zfs', 'clone', base, name])
    try:
        shutil.copyfile('/etc/resolv.conf', os.path.join(zfs_mountpoint(name), 'etc/resolv.conf'))
        jail_run(zfs_mountpoint(name), args.command)
        # subprocess.check_output(['jail', '-c', 'interface=lo1', 'ip4.addr=127.0.1.0', 'path=' + zfs_mountpoint(name), 'command', command])
    finally:
        subprocess.run(['umount', zfs_mountpoint(name) + '/dev'])
        zfs_run(['zfs', 'destroy', '-f', name])
        # raise
