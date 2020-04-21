from zfs import *


def new_snapshot(base, fun, name):
    type_ = zfs_get_type(base)
    if type_ != 'snapshot':
        raise ValueError('Provided base dataset is not a snapshot')
    if '/' not in name:
        root = '/'.join(base.split('/')[:-1])
        name = root + '/' + name
    zfs_run(['zfs', 'clone', base, name])
    try:
        fun()
    except:
        zfs_run(['zfs', 'destroy', name])
        raise
    zfs_run(['zfs', 'set', 'readonly=on', name])
    zfs_run(['zfs', 'snapshot', name + '@1'])