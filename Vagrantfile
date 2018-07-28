# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.box = "reahl/bionic64"

  config.vm.network "forwarded_port", guest: 5433, host: 5433

  config.vm.provision "shell", inline: <<-SHELL
   export DEBIAN_FRONTEND=noninteractive
   apt-get update
   apt-get install -y gdb libpam0g-dev
   /vagrant/gemstone/installGemStone.sh 3.4.1
  SHELL

  config.vm.provision "shell", privileged: false, inline: <<-SHELL
   /vagrant/scripts/setupGit.sh
   /vagrant/gemstone/defineGemStoneEnvironment.sh 3.4.1
   mkdir -p ~/.reahlworkspace/dist-egg
   pip install cython
  SHELL
end
