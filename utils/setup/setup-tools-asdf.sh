#!/bin/bash
set -e

echo "Setting up prerequisites in WSL2..."
sudo apt update && sudo apt install -y curl git

echo "Installing asdf..."
git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.14.1
echo -e '\n. $HOME/.asdf/asdf.sh' >> ~/.bashrc
source ~/.bashrc

echo "Adding asdf plugins..."
asdf plugin add kubectl https://github.com/asdf-community/asdf-kubectl.git
asdf plugin add helm https://github.com/Antiarchitect/asdf-helm.git
asdf plugin add minikube https://github.com/alvarobp/asdf-minikube.git
asdf plugin add git

echo "Installing tools..."
asdf install kubectl latest
asdf install helm latest
asdf install minikube latest
asdf install git latest

echo "Setting global versions..."
asdf global kubectl $(asdf latest kubectl)
asdf global helm $(asdf latest helm)
asdf global minikube $(asdf latest minikube)
asdf global git $(asdf latest git)

echo "Please install Docker Desktop manually and enable WSL2 integration."
echo "Verify installations:"
kubectl version --client
helm version
minikube version
git --versions