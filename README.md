# DevOps Days Scripts

The purpose of this repo is show a demo of provisioning servers through BMC API.

This script provides a spark cluster of 3 Ubuntu servers (1 master node and 2 workers nodes).

To run the script you need a valid API credentials for https://api.phoenixnap.com/bmc/v0/

### Requirements

- Python 3 (https://www.python.org/downloads/)

- Valid API credentials

### Setup

1. Download the repo ```git clone git@gitlab.com:phoenixnap/bare-metal-cloud/devops-days-scritps.git```

2. Open the branch ```spark```

3. Set your credentials in credentials.conf

4. Set default public key in server-settings.conf, you can get it with ```cat ~/.ssh/id_rsa.pub```

5. Execute the command ```python3 bmc-spark.py```

### Script details

##### URL
After prepare the infrastructure, software and check that the cluster is correctly setup, the script will be provide an URL to access to the master node UI


### After the demo

Please release the servers with the command ```python3 bmc-spark.py -d0```