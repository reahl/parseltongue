#!/bin/bash -ex

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <gemstone_version>"
    exit 1
fi

VERSION=$1
ARCH=x86_64

#Download and unzip gemstone
[ -e $DEV_HOME/testdownloads ] || mkdir -p $DEV_HOME/testdownloads 

DOWNLOADED=$DEV_HOME/testdownloads/GemStone64Bit${VERSION}-${ARCH}.Linux.zip
if [ ! -e $DOWNLOADED ]; then
 wget -nv -O  $DOWNLOADED "https://downloads.gemtalksystems.com/pub/GemStone64/${VERSION}/GemStone64Bit${VERSION}-${ARCH}.Linux.zip"
fi 

mkdir -p /opt/gemstone
chmod 775 /opt/gemstone
unzip $DOWNLOADED -d /opt/gemstone

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
#Set the Environment
echo ""  >> /etc/environment
export GEMSTONE=/opt/gemstone/GemStone64Bit${VERSION}-${ARCH}.Linux

#setup key file
cp $GEMSTONE/sys/community.starter.key $GEMSTONE/sys/gemstone.key

#Define the NetLDI Service
echo ""  >> /etc/services
echo "gs64ldi         5433/tcp                        #GemStone/S"  >> /etc/services

#run installation
if [ -z "$CI" ]; then
  SOURCE_ROOT=/opt/dev
else
  SOURCE_ROOT="$(pwd)"
fi

cd $GEMSTONE/install
$SOURCE_ROOT/gemstone/answersForInstallgs.sh | $GEMSTONE/install/installgs 

#group and urser
chgrp -R $DEV_USER $GEMSTONE
chown -R $DEV_USER $GEMSTONE
chmod 775 /opt/gemstone

ln -s $GEMSTONE/lib/libicudata.54.1.so $GEMSTONE/lib/libicudata.so.54
ln -s $GEMSTONE/lib/libicui18n.54.1.so $GEMSTONE/lib/libicui18n.so.54
ln -s $GEMSTONE/lib/libicuuc.54.1.so $GEMSTONE/lib/libicuuc.so.54
ln -s $GEMSTONE/lib/libgbjgci313-$VERSION-64.so $GEMSTONE/lib/libgbjgci313.so

sed -i 's/^#GEM_NATIVE_CODE_ENABLED = 2;/GEM_NATIVE_CODE_ENABLED = 0;/' $GEMSTONE/data/system.conf

