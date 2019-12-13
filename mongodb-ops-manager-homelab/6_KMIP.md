# KMIP  __TODO__

- Note: Following the steps listed [here](https://github.com/OpenKMIP/PyKMIP)
- Note: This is being installed on `kmip.cloud` at `10.18.89.4`
- Install PyKMIP

    ```bash
    yum install -y git
    yum --enablerepo=extras install epel-release
    yum install -y python-pip
    pip install --upgrade pip

    git clone https://github.com/OpenKMIP/PyKMIP
    cd /root/PyKMIP
    pip install -r requirements.txt

    python setup.py build
    python setup.py install
    ```