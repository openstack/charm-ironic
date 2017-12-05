#
# Copyright 2015 Cloudbase Solutions SRL
#

from charmhelpers.contrib.openstack import context
from charmhelpers.contrib.openstack.ip import DEPLOY, resolve_address

from charmhelpers.core.hookenv import (
    config,
    relation_get,
    relation_ids,
    related_units,
    unit_get,
    log,
    INFO,
)
from netaddr import IPNetwork, IPAddress
import constants
import os
import netifaces


def interfaces_by_mac():
    """Returns a list of all interfaces connected to the machine with their
       associated MAC address.
    """
    ret = {}
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        details = netifaces.ifaddresses(interface).get(netifaces.AF_LINK)
        if details:
            addr = details[0]["addr"]
            ret[addr.upper()] = interface
    return ret


class GlanceSwiftBackendContext(context.OSContextGenerator):

    def __call__(self):
        rids = relation_ids('image-service')
        if not rids:
            return {}

        identity_ctxt = context.IdentityServiceContext(service='ironic',
                                                       service_user='ironic')()
        if not identity_ctxt:
            return {}

        ctxt = {}
        for rid in rids:
            for unit in related_units(rid):
                ctxt = {
                    'glance_swift_account':
                        config('swift-account') or 'AUTH_%s' % identity_ctxt['admin_tenant_id'],
                    'glance_swift_container':
                        config('swift-container') or relation_get('swift-container', rid=rid, unit=unit),
                    'glance_swift_temp_url_key':
                        config('swift-temp-url-key') or relation_get('swift-temp-url-key', rid=rid, unit=unit),
                    'glance_swift_temp_url_duration':
                        config('swift-temp-url-duration')
                }

        missing = [k for k, v in ctxt.iteritems() if not v]
        if missing:
            log("GlanceSwiftBackend context is incomplete. Missing required "
                "relation data: %s" % (' '.join(missing)), level=INFO)
            return {}

        return ctxt


class ObjectStoreContext(context.OSContextGenerator):
    interfaces = ['object-store']

    def __call__(self):
        if config('swift-url'):
            return {'swift_url': config('swift-url')}

        for rid in relation_ids('object-store'):
            for unit in related_units(rid):
                url = relation_get('swift-url', rid=rid, unit=unit)
                if url:
                    return {'swift_url': url}
        return {}


class NeutronContext(context.OSContextGenerator):
    interfaces = ['neutron-api']

    def __call__(self):
        for rid in relation_ids('neutron-api'):
            for unit in related_units(rid):
                url = relation_get('neutron-url', rid=rid, unit=unit)
                if url:
                    return {'neutron_url': url}
        return {}


class IronicContext(context.OSContextGenerator):

    def __call__(self):
        uefi_pxe_bootfile_name = config('uefi-pxe-bootfile-name') or \
                                 'bootx64.efi'
        uefi_pxe_config_template = config('uefi-pxe-config-template') or \
            '$pybasedir/drivers/modules/pxe_grub_config.template'

        pxe_bootfile_name = config('pxe-bootfile-name')
        if not pxe_bootfile_name:
            if config('enable-ipxe'):
                pxe_bootfile_name = 'undionly.kpxe'
            else:
                pxe_bootfile_name = 'pxelinux.0'

        pxe_config_template = config('pxe-config-template')
        if not pxe_config_template:
            if config('enable-ipxe'):
                pxe_config_template = \
                    '$pybasedir/drivers/modules/ipxe_config.template'
            else:
                pxe_config_template = \
                    '$pybasedir/drivers/modules/pxe_config.template'

        ipxe_boot_script = config('ipxe-boot-script')
        if not ipxe_boot_script:
            ipxe_boot_script = '$pybasedir/drivers/modules/boot.ipxe'

        ctxt = {
            'tftp_server': resolve_address(DEPLOY),
            'tftp_root': constants.TFTP_ROOT,
            'pxelinux_cfg_root': constants.PXELINUX_CFG_ROOT,
            'ironic_api_port': constants.API_PORTS['ironic-api'],
            'ipxe_enabled': config('enable-ipxe'),
            'enabled_drivers': config('enabled-drivers'),
            'nodes_cleaning': config('nodes-cleaning'),
            'dhcp_provider': config('dhcp-provider'),
            'disk_devices': config('disk-devices'),
            'deploy_network_uuid': config('deploy-network-uuid'),
            'cleaning_network_uuid': config('cleaning-network-uuid'),
            'pxe_bootfile_name': pxe_bootfile_name,
            'pxe_config_template': pxe_config_template,
            'ipxe_boot_script': ipxe_boot_script,
            'uefi_pxe_bootfile_name': uefi_pxe_bootfile_name,
            'uefi_pxe_config_template': uefi_pxe_config_template,
            'ipa_api_url': "http://{}:{}".format(resolve_address(DEPLOY), constants.API_PORTS['ironic-api'])
        }

        return ctxt


class NginxContext(context.OSContextGenerator):

    def __call__(self):
        ctxt = {
            'http_root': constants.HTTP_ROOT,
            'http_port': config('http-port'),
            'http_url': 'http://{}:{}'.format(resolve_address(DEPLOY),
                                              config('http-port')),
            'server_name': constants.IRONIC_VHOST_NAME
        }

        return ctxt


class TFTPContext(context.OSContextGenerator):

    def __call__(self):
        tftp_root = constants.TFTP_ROOT
        map_file = os.path.join(tftp_root, 'map-file')
        tftp_options = '-v --map-file %s' % map_file

        return {
            'tftp_username': 'ironic',
            'tftp_directory': tftp_root,
            'tftp_address': '0.0.0.0',
            'tftp_port': config('tftp-port'),
            'tftp_options': tftp_options,
        }
