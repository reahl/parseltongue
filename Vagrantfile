# -*- mode: ruby -*-
# vi: set ft=ruby :

# To use vagrant on ubuntu 16.04:
#  apt-get install vagrant vagrant-lxc vagrant-cachier
#  cd <where VagrantFile is>
#  vagrant up
#  vagrant ssh

Vagrant.configure("2") do |config|

  config.vm.box = "reahl/xenial64"

  config.vm.network "forwarded_port", guest: 8000, host: 8000
  config.vm.network "forwarded_port", guest: 8363, host: 8363

 config.vm.provision "shell", inline: <<-SHELL
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y gdb
  /vagrant/gemstone/systemChanges.sh
 SHELL
 #config.vm.provision :shell, path: "/vagrant/gemstone/systemChanges.sh"
 config.vm.provision "shell", privileged: false, inline: <<-SHELL
  /vagrant/gemstone/gemPath.sh
  SHELL
end
