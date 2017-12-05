#
# Copyright 2015 Cloudbase Solutions SRL
#

PACKAGES = {
    'CORE': [
        'ironic-api',
        'ironic-conductor',
        'python-ironicclient',
        'tftpd-hpa',
        'syslinux-common',
        'syslinux',
        'pxelinux',
        'ipmitool',
        'python-mysqldb'
    ],
    'iPXE': [
        'ipxe',
        'nginx'
    ],
    'UEFI': [
        'grub-efi-amd64-signed',
        'shim-signed'
    ]
}

API_PORTS = {
    'ironic-api': 6385,
}

IRONIC_USER = 'ironic'
TEMPLATES_DIR = 'templates'
IRONIC_CONF_DIR = '/etc/ironic'
IRONIC_CONF = '%s/ironic.conf' % IRONIC_CONF_DIR
TFTP_CONF = '/etc/default/tftpd-hpa'
TFTP_ROOT = '/tftpboot'
TFTP_SERVICE_NAME = 'tftpd-hpa'
HTTP_ROOT = '/httpboot'
NGINX_SERVICE_NAME = 'nginx'
NGINX_SITES_AVAILABLE = '/etc/nginx/sites-available'
NGINX_SITES_ENABLED = '/etc/nginx/sites-enabled'
HTTPBOOT_AVAILABLE = '%s/httpboot' % NGINX_SITES_AVAILABLE
HTTPBOOT_ENABLED = '%s/httpboot' % NGINX_SITES_ENABLED
DEFAULT_SITE_ENABLED = '%s/default' % NGINX_SITES_ENABLED
IRONIC_VHOST_NAME = 'ironic_server'
GRUB_DIR = '%s/grub' % TFTP_ROOT
PXELINUX_CFG_ROOT = '%s/pxelinux.cfg' % TFTP_ROOT
PXELINUX_CONF = '%s/default' % PXELINUX_CFG_ROOT

TFTP_FILES = {
    'PXE': {
        'map-file': '%s/map-file-pxe' % TEMPLATES_DIR,
        'chain.c32': '/usr/lib/syslinux/modules/bios/chain.c32',
        'pxelinux.0': '/usr/lib/PXELINUX/pxelinux.0',
        'ldlinux.c32': '/usr/lib/syslinux/modules/bios/ldlinux.c32',
        'libutil.c32': '/usr/lib/syslinux/modules/bios/libutil.c32',
        'libcom32.c32': '/usr/lib/syslinux/modules/bios/libcom32.c32'
    },
    'iPXE': {
        'map-file': '%s/map-file-ipxe' % TEMPLATES_DIR,
        'undionly.kpxe': '/usr/lib/ipxe/undionly.kpxe'
    },
    'UEFI': {
        'bootx64.efi': '/usr/lib/shim/shim.efi.signed',
        'grubx64.efi': '/usr/lib/grub/x86_64-efi-signed/grubnetx64.efi.signed',
        'grub/grub.cfg': '%s/grub.cfg' % TEMPLATES_DIR,
    }
}
