#!/bin/bash -ev

#Download and unzip gemstone
mkdir -p /opt/gemstone

[ -e $HOME/testdownloads ] || mkdir -p $HOME/testdownloads 

cd /opt/gemstone

if [ ! -e $HOME/testdownloads/GemStone64Bit3.3.3-x86_64.Linux.zip ]; then
 wget -nv -O  $HOME/testdownloads/GemStone64Bit3.3.3-x86_64.Linux.zip 'https://downloads.gemtalksystems.com/pub/GemStone64/3.3.3/GemStone64Bit3.3.3-x86_64.Linux.zip'
fi 

unzip $HOME/testdownloads/GemStone64Bit3.3.3-x86_64.Linux.zip

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
#Set the Environment
#echo ""  >> /etc/environment
#echo "GEMSTONE=/opt/gemstone/GemStone64Bit3.3.3-x86_64.Linux" >> /etc/environment
GEMSTONE=/opt/gemstone/GemStone64Bit3.3.3-x86_64.Linux
export GEMSTONE

#shared memory and semaphores
#echo ""  >> /etc/sysctl.conf
#echo "kernel.shmall  =  1572864" >> /etc/sysctl.conf
#echo "kernel.shmmax  =  6442450944" >> /etc/sysctl.conf
#echo "kernel.sem=1000  512000  64  2048" >> /etc/sysctl.conf

#pam
echo "" >> /etc/pam.d/other
echo "auth		required	pam_ldap.so" >> /etc/pam.d/other

#Large Memory Pages
echo "" >>  /etc/sysctl.conf
echo  "vm.nr_hugepages=10464" >>  /etc/sysctl.conf
#Configure the executables to use large pages:
/sbin/setcap cap_ipc_lock=pe $GEMSTONE/sys/startshrpcmon
/sbin/setcap cap_ipc_lock=pe $GEMSTONE/sys/shrpcmonitor

#Prepare for Installation
[ -e /dev/raw ] || mkdir -p /dev/raw
[ -e /etc/services ] || mkdir -p /etc/services
[ -e /usr/gemstone ] || mkdir -p /usr/gemstone 

#setup key file
cp /opt/gemstone/GemStone64Bit3.3.3-x86_64.Linux/sys/community.starter.key /opt/gemstone/GemStone64Bit3.3.3-x86_64.Linux/sys/gemstone.key
#chmod 555 $GEMSTONE/sys
#chmod 555 $GEMSTONE/sys/gemstone.key

#Define the NetLDI Service
echo ""  >> /etc/services
echo "gs64ldi         5433/tcp                        #GemStone/S 64 Bit 3.3.3"  >> /etc/services

#run installation
/vagrant/gemstone/installgs 
