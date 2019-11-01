#/bin/bash
sudo ln -s $(pwd)/rezeptbuch.service /etc/systemd/system/rezeptbuch.service
sudo systemctl daemon-reload
sudo systemctl enable rezeptbuch
sudo systemctl start rezeptbuch
