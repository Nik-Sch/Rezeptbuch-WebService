#/bin/bash
ln -s $(pwd)/rezeptbuch.service /home/$(whoami)/.config/systemd/user/rezeptbuch.service
systemctl --user daemon-reload
systemctl --user enable rezeptbuch
systemctl --user start rezeptbuch
