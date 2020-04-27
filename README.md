# Focker

## Introduction

Focker is a FreeBSD image orchestration tool in the vein of Docker.

## Installation

In order to use Focker you need a ZFS pool available in your FreeBSD installation.

### Installing the Python package

Run:

```bash
git clone https://github.com/sadaszewski/focker.git
cd focker/
python setup.py install
```

or (if you want an uninstaller):

```bash
git clone https://github.com/sadaszewski/focker.git
cd focker/
python setup.py sdist
pip install dist/focker-0.9.tgz
```

### Setting up ZFS

Upon first execution of the `focker` command, Focker will automatically create the necessary directories and ZFS datasets. You just need to exclude the unlikely case that you are already using /focker in your filesystem hierarchy. The layout after initialization will look the following:

```
/focker
/focker/images
/focker/jails
/focker/volumes
```

`images`, `jails`, and `volumes` have corresponding ZFS datasets with `canmount=off` so that they serve as mountpoint anchors for child entries.

### Preparing base image

To bootstrap the images system you need to install FreeBSD in jail mode to a ZFS dataset placed in /focker/images and provide two user-defined properties - `focker:sha256` and `focker:tags`. One way to achieve this would be the following:

```bash
TAGS="freebsd-latest freebsd-$(freebsd-version | cut -d'-' -f1)"
VERSION="FreeBSD $(freebsd-version)"
SHA256=$(echo -n ${VERSION} | sha256)
NAME=${SHA256:0:7}
zfs create -o focker:sha256=${SHA256} -o focker:tags="${TAGS}" zroot/focker/images/${NAME}
bsdinstall jail /focker/images/${NAME}
zfs set readonly=on zroot/focker/images/${NAME}
zfs snapshot zroot/focker/images/${NAME}@1
```

## Usage

At this point, Focker is ready to use.

### `focker` command syntax

```
focker
|- image
|  |- build
|  |  |- focker_dir
|  |  `- --tags|-t TAG [...]
|  |- tag
|  |  |- reference
|  |  `- TAG [...]
|  |- untag
|  |  `- TAG [...]
|  |- list
|  |  `- --full-sha256|-f
|  |- prune
|  `- remove
|  |  |- reference
|  |  `- --remove-dependents|-R
|- jail
|  |- create
|  |- start
|  |- stop
|  |- remove
|  |- exec
|  |- oneshot
|  |- list
|  |- tag
|  |- untag
|  `- prune
|- volume
|  |- create
|  |- prune
|  |- list
|  |- tag
|  `- untag
`- compose
   |- build
   `- run
```
