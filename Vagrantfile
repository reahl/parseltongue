# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.box = "reahl/xenial64"

  config.vm.network "forwarded_port", guest: 5433, host: 5433

  config.vm.provision "shell", inline: <<-SHELL
   export DEBIAN_FRONTEND=noninteractive
   apt-get update
   apt-get install -y gdb
   apt-get install -y libpam0g-dev
   /vagrant/gemstone/installGemStone.sh
  SHELL

  config.vm.provision "shell", privileged: false, inline: <<-SHELL
   /vagrant/gemstone/defineGemStoneEnvironment.sh
   mkdir ~/.reahlworkspace
   touch ~/.reahlworkspace/dist-egg
   pip install cython
   pip install pytest
   pip install reahl.component
  SHELL
end
