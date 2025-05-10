# Notes for Linux on Asus Adol 14

## Suspend issues

`/boot/grub/grub.cfg`

```
acpi.ec_no_wakeup=1
```

## Wifi and bluetooth resume

`/etc/systemd/system/rfkill-suspend.service`
```
[Unit]
Description=Stop network interface when suspending
Before=sleep.target
StopWhenUnneeded=yes

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=-/usr/bin/rfkill block all
ExecStop=-/usr/bin/rfkill unblock wifi

[Install]
WantedBy=sleep.target
```

## Wifi disconnection and reconnection issues

`/etc/NetworkManager/conf.d/default-wifi-powersave-on.conf`

```
[connection]
wifi.powersave = 2
```