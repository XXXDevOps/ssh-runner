set -e

echo "Init action"

## reload systemctl
systemctl daemon-reload
## enable service after system boot or reboot
systemctl enable sqe_dj.service
