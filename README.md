Creates virtual com ports on linux to allow sharing the ICOM CI-V controlled equipment across multiple applications

### Example systemd unit file
```ini
[Unit]
Description=civmux
After=syslog.target


[Service]
ExecStart=/usr/bin/python3 -m civmux
Restart=always
RestartSec=3
WorkingDirectory=/home/pi
User=root
SyslogIdentifier=civmux
Type=notify

[Install]
WantedBy=multi-user.target
```

```
usage: ICOM CIV Mux [-h] [-c COUNT] [-d DEVICE] [--symlink-path SYMLINK_PATH] [-b BAUD_RATE]

Creates virtual serial ports so multiple applications can control the radio at once

optional arguments:
  -h, --help            show this help message and exit
  -c COUNT, --count COUNT
                        Number of virtual ports to create
  -d DEVICE, --device DEVICE
                        Serial port for the radio
  --symlink-path SYMLINK_PATH
                        The path prefix for creating symlinks to pts devices
  -b BAUD_RATE, --baud-rate BAUD_RATE
                        Baud rate of the radio
```