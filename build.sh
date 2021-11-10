#!/bin/bash
set -e;
RUNDIR="`dirname \"$0\"`"

echo "Build Windows version"
sudo docker run -it --name electrum-wine-builder-cont -v $PWD:/opt/wine64/drive_c/electrum-scribe --rm --workdir /opt/wine64/drive_c/electrum-scribe/contrib/build-wine coinfactorybot/electrum-desktop-build-environmnet:mona-win ./build.sh
mkdir -p $RUNDIR/dist/windows
sudo mv $RUNDIR/contrib/build-wine/dist/* $RUNDIR/dist/windows
sudo chown -R $(whoami):$(whoami) $RUNDIR/dist


echo "Build OSX version"
