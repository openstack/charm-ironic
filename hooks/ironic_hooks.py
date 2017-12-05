#
# Copyright 2015 Cloudbase Solutions SRL
#

from charmhelpers.core.hookenv import (
    config,
    relation_ids,
    open_port,
    close_port,
    unit_get,
    is_leader,
    log,
    relation_set,
    status_set,
)
from charmhelpers.core.host import (
    restart_on_change,
)
from charmhelpers.contrib.openstack.ip import (
    canonical_url,
    PUBLIC, INTERNAL, ADMIN
)
from charmhelpers.fetch import (
    apt_install,
    apt_update,
)
from charmhelpers.contrib.openstack.utils import (
    configure_installation_source,
    openstack_upgrade_available,
)
from charmhelpers.contrib.openstack import (
    context,
)
from ironic_utils import (
    register_configs,
    cmd_all_services,
    restart_map,
    determine_ports,
    migrate_ironic_database,
    set_up_pxe,
    do_openstack_upgrade,
    write_all_configs
)
import constants

CONFIGS = register_configs()


def install():
    configure_installation_source(config('openstack-origin'))
    apt_update()
    apt_install(constants.PACKAGES['CORE'], fatal=True)


@restart_on_change(restart_map())
def config_changed():
    additional_pkgs = []
    if config('enable-ipxe'):
        additional_pkgs += constants.PACKAGES['iPXE']
    if config('enable-uefi'):
        additional_pkgs += constants.PACKAGES['UEFI']
    if len(additional_pkgs) > 0:
        apt_update()
        apt_install(additional_pkgs, fatal=True)

    if openstack_upgrade_available('ironic-common'):
        do_openstack_upgrade(CONFIGS)

    write_all_configs(CONFIGS)

    set_up_pxe()


def start():
    cmd_all_services('start')
    [open_port(port) for port in determine_ports()]


def stop():
    [close_port(port) for port in determine_ports()]
    cmd_all_services('stop')


def identity_joined(relation_id=None):
    relation_data = {
        'service': 'ironic',
        'region': config('region'),
        'public_url': '{}:{}'.format(canonical_url(CONFIGS, PUBLIC),
                                     constants.API_PORTS['ironic-api']),
        'admin_url': '{}:{}'.format(canonical_url(CONFIGS, ADMIN),
                                    constants.API_PORTS['ironic-api']),
        'internal_url': '{}:{}'.format(canonical_url(CONFIGS, INTERNAL),
                                       constants.API_PORTS['ironic-api'])
    }
    relation_set(relation_id=relation_id, **relation_data)


@restart_on_change(restart_map())
def identity_changed():
    if 'identity-service' not in CONFIGS.complete_contexts():
        log('identity-service relation incomplete. Peer not ready?')
        return
    write_all_configs(CONFIGS)
    [ironic_api_joined(r_id) for r_id in relation_ids('ironic-api')]


def amqp_joined(relation_id=None):
    relation_set(relation_id=relation_id,
                 username=config('rabbit-user'),
                 vhost=config('rabbit-vhost'))


@restart_on_change(restart_map())
def amqp_changed():
    if 'amqp' not in CONFIGS.complete_contexts():
        log('amqp relation incomplete. Peer not ready?')
        return
    write_all_configs(CONFIGS)


@restart_on_change(restart_map())
def image_service_changed():
    if 'image-service' not in CONFIGS.complete_contexts():
        log('image-service relation incomplete. Peer not ready?')
        return
    write_all_configs(CONFIGS)


@restart_on_change(restart_map())
def object_store_changed():
    if 'object-store' not in CONFIGS.complete_contexts():
        log('object-store relation incomplete. Peer not ready?')
        return
    write_all_configs(CONFIGS)


def db_joined(relation_id=None):
    relation_set(relation_id=relation_id,
                 database=config('database'),
                 username=config('database-user'),
                 hostname=unit_get('private-address'))


@restart_on_change(restart_map())
def db_changed():
    if 'shared-db' not in CONFIGS.complete_contexts():
        log('shared-db relation incomplete. Peer not ready?')
        return
    write_all_configs(CONFIGS)
    if is_leader():
        migrate_ironic_database()


def ironic_api_joined(relation_id=None):
    if 'identity-service' not in CONFIGS.complete_contexts():
        log('identity-service relation incomplete. Cannot set ironic-api '
            'relation without identity-service relation.')
        return

    identity_ctxt = context.IdentityServiceContext(service='ironic',
                                                   service_user='ironic')()
    relation_data = {
        'ironic_api_server':
        "{}:{}".format(canonical_url(CONFIGS, INTERNAL),
                       constants.API_PORTS['ironic-api']),
        'admin_user': identity_ctxt['admin_user'],
        'admin_password': identity_ctxt['admin_password'],
        'auth_protocol': identity_ctxt['auth_protocol'] or 'http',
        'auth_host': identity_ctxt['auth_host'],
        'auth_port': identity_ctxt['auth_port'],
        'admin_tenant_name': identity_ctxt['admin_tenant_name'],
        'api_protocol': 'http',
        'api_host': unit_get('private-address'),
        'api_port': constants.API_PORTS['ironic-api'],
    }

    relation_set(relation_id=relation_id, **relation_data)
    log('Done joining ironic-api. Signalling readiness to juju.')
    status_set('active', 'Ready.')


@restart_on_change(restart_map())
def neutron_api_changed():
    if 'neutron-api' not in CONFIGS.complete_contexts():
        log('neutron-api relation is incomplete.')
        return
    write_all_configs(CONFIGS)


@restart_on_change(restart_map())
def relation_broken():
    write_all_configs(CONFIGS)
