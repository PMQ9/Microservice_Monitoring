#!/bin/bash
set -e

echo "Installing prerequisites..."
sudo apt update
sudo apt install -y curl wget

echo "Installing Docker..."
sudo apt install -y docker.io
sudo usermod -aG docker $USER

echo "Installing kubectl..."
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

echo "Installing Helm..."
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

echo "Installing Minikube..."
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
chmod +x minikube-linux-amd64
sudo mv minikube-linux-amd64 /usr/local/bin/minikube

echo "Installing Git..."
sudo apt install -y git

echo "Verifying installations..."
kubectl version --client
helm version
minikube version
docker --version
git --version

echo "Setup complete! Note: Install Docker Desktop for better WSL2 integration."
echo "Log out and back in for Docker group changes."