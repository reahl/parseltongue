#!/bin/bash -e

#install in ~/bin/ mby?

VERSION=3.3.3
#VERSION=3.4.0
ARCH=x86_64

#Download and unzip gemstone
mkdir -p /opt/gemstone

export VAGRANT_HOME=/home/vagrant

[ -e $VAGRANT_HOME/testdownloads ] || mkdir -p $VAGRANT_HOME/testdownloads 

DOWNLOADED=$VAGRANT_HOME/testdownloads/GemStone64Bit${VERSION}-${ARCH}.Linux.zip
if [ ! -e $DOWNLOADED ]; then
 wget -nv -O  $DOWNLOADED "https://downloads.gemtalksystems.com/pub/GemStone64/${VERSION}/GemStone64Bit${VERSION}-${ARCH}.Linux.zip"
fi 

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
if [ -e /vagrant ]; then
  INSTALLDIR=/vagrant
else
  INSTALLDIR="$(pwd)"
fi

cd $GEMSTONE/install
$INSTALLDIR/gemstone/answersForInstallgs.sh | $GEMSTONE/install/installgs 

#group and urser
chgrp -R vagrant $GEMSTONE
chown -R vagrant $GEMSTONE

ln -s $GEMSTONE/lib/libicudata.54.1.so $GEMSTONE/lib/libicudata.so.54
ln -s $GEMSTONE/lib/libicui18n.54.1.so $GEMSTONE/lib/libicui18n.so.54
ln -s $GEMSTONE/lib/libicuuc.54.1.so $GEMSTONE/lib/libicuuc.so.54
ln -s $GEMSTONE/lib/libgbjgci313-3.3.3-64.so $GEMSTONE/lib/libgbjgci313.so
