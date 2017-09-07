#!/bin/bash -e

#install in ~/bin/ mby?

#Download and unzip gemstone
mkdir -p /opt/gemstone

[ -e $HOME/testdownloads ] || mkdir -p $HOME/testdownloads 

export VAGRANT_HOME=/home/vagrant

if [ ! -e $VAGRANT_HOME/testdownloads/GemStone64Bit3.3.3-x86_64.Linux.zip ]; then
 wget -nv -O  $VAGRANT_HOME/testdownloads/GemStone64Bit3.3.3-x86_64.Linux.zip 'https://downloads.gemtalksystems.com/pub/GemStone64/3.3.3/GemStone64Bit3.3.3-x86_64.Linux.zip'
fi 

unzip $VAGRANT_HOME/testdownloads/GemStone64Bit3.3.3-x86_64.Linux.zip -d /opt/gemstone

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
#Set the Environment
#echo ""  >> /etc/environment
#echo "GEMSTONE=/opt/gemstone/GemStone64Bit3.3.3-x86_64.Linux" >> /etc/environment
export GEMSTONE=/opt/gemstone/GemStone64Bit3.3.3-x86_64.Linux

#setup key file
cp $GEMSTONE/sys/community.starter.key $GEMSTONE/sys/gemstone.key

#Define the NetLDI Service
echo ""  >> /etc/services
echo "gs64ldi         5433/tcp                        #GemStone/S 64 Bit 3.3.3"  >> /etc/services

#run installation
cd $GEMSTONE/install
/vagrant/gemstone/answersForInstallgs.sh | $GEMSTONE/install/installgs 

#group and urser
chgrp -R vagrant $GEMSTONE
chown -R vagrant $GEMSTONE