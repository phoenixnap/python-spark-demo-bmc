#!/bin/bash

echo "Setting up /etc/hosts"
sudo sed -i -e 's/127.0.1.1/'"$1"'/g' /etc/hosts
echo "Installing jdk, scala and git"
sudo apt -qq -y install default-jdk scala git > /dev/null
echo "Downloading spark-2.4.5"
wget https://downloads.apache.org/spark/spark-2.4.5/spark-2.4.5-bin-hadoop2.7.tgz -q
echo "Unzipping spark-2.4.5"
tar xf spark-2.4.5-bin-hadoop2.7.tgz
sudo mv spark-2.4.5-bin-hadoop2.7 /opt/spark
echo "Setting up environment variables"
echo "export SPARK_HOME=/opt/spark" >> ~/.bashrc
echo "export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin" >> ~/.bashrc
echo "export PYSPARK_PYTHON=/usr/bin/python3" >> ~/.bashrc
echo "JAVA_HOME=\"/usr/lib/jvm/default-java\"" >> ~/.bashrc
source ~/.bashrc
exit
