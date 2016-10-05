#!/bin/sh

USAGE="Usage: $(basename $0) -v version [-h]"

while getopts "hv:" cliopts
do
    case "$cliopts" in
    h)  echo $USAGE;
        exit 0;;
    v)  VERSION="$OPTARG";;
    \?) echo $USAGE;
        exit 1;;
    esac
done

if [ "$VERSION" = '' ];
then
    echo "You must specify the new version."
    exit 1
fi



cd /usr/local/uravo/config
if [ -f db-update.sql ]; then
    mv db-update.sql db-update-$VERSION.sql
    git add db-update-$VERSION.sql
fi
echo $VERSION > version.txt

cd /usr/local/uravo/build
sed -i "s/Version: .*/Version: ${VERSION}/" uravo.spec

