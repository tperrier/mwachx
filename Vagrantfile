# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "bento/ubuntu-16.04"
  config.vm.hostname = "mwach"
  
  # forward http
  config.vm.network "forwarded_port", host: 8000, guest: 8000

  config.vm.provision :shell, :inline => "sudo apt-get update && sudo DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::=\"--force-confdef\" -o Dpkg::Options::=\"--force-confold\" upgrade", run: "once"
  config.vm.provision :shell, :inline => "curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -", run: "once"
  config.vm.provision :shell, :inline => "sudo apt-get install -y nodejs build-essential dos2unix python-virtualenv", run: "once"
  config.vm.provision :shell, :inline => "dos2unix /vagrant/vagrant-provision.sh", run: "once"
  config.vm.provision :shell, :inline => "sudo bash /vagrant/vagrant-provision.sh", run: "once"

  config.vm.provider "virtualbox" do |v|
	v.memory = 1024
	v.cpus = 2
  end
end
