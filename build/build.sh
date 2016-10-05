#!/bin/bash

USAGE="Usage: $(basename $0) [-h]"

while getopts "h" cliopts
do
    case "$cliopts" in
    h)  echo $USAGE;
        exit 0;;
    \?) echo $USAGE;
        exit 1;;
    esac
done

set -x

VERSION=`cat /usr/local/uravo/config/version.txt`;
if [ "$VERSION" = '' ];
then
    echo "Cannot determine version number."
    exit 1
fi

PACKAGE_NAME="uravo-$VERSION"

LIVE_DIR="/usr/local/uravo";
BUILD_DIR="/tmp"
BASE_DIR="$BUILD_DIR/$PACKAGE_NAME"
ROOT_DIR="$BASE_DIR/$LIVE_DIR"

[ -f $SOURCE_DIR/$PACKAGE_NAME.tar.gz ] && rm -f $SOURCE_DIR/$PACKAGE_NAME.tar.gz
[ -d $ROOT_DIR ] && rm -rf $ROOT_DIR
mkdir -p $ROOT_DIR

cp -a /usr/local/uravo/* $ROOT_DIR
mkdir -p $BASE_DIR/etc/cron.d
cat > $BASE_DIR/etc/cron.d/uravo <<__EOF__
* * * * *   root /bin/touch /var/run/crond.running > /dev/null 2>&1
*/5 * * * * root $LIVE_DIR/bin/agent.pl > /tmp/agent.pl.log 2>&1
45 3 * * *  root $LIVE_DIR/bin/update_uravo.pl > /tmp/update_uravo.pl.rpm.log 2>&1
__EOF__
chmod 644 $BASE_DIR/etc/cron.d/uravo

cd $BUILD_DIR
tar -c -v -z --exclude='.git' --exclude='build' -f ${PACKAGE_NAME}.tar.gz $PACKAGE_NAME/
cp ${PACKAGE_NAME}.tar.gz ~/SOURCES/

rm -rf $BASE_DIR
rpmbuild -ba /usr/local/uravo/build/uravo.spec

cd $HOME
RPM="uravo-$VERSION-1.noarch.rpm"
RELEASE_DIR="/usr/local/www/uravo.org/html";
cp RPMS/noarch/$RPM $RELEASE_DIR/
rm -f $RELEASE_DIR/uravo-latest.noarch.rpm
ln -s $RELEASE_DIR/$RPM $RELEASE_DIR/uravo-latest.noarch.rpm


