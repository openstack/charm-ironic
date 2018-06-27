#
# Copyright 2015 Cloudbase Solutions SRL
#

from charmhelpers.core.hookenv import (
    config,
    log,
)
from charmhelpers.contrib.openstack import (
    templating,
    context,
)
from charmhelpers.contrib.openstack.utils import (
    os_release,
    get_os_codename_install_source,
    configure_installation_source,
)
from charmhelpers.core.host import (
    service,
    service_start,
    service_running,
    service_reload
)
from ironic_context import (
    IronicContext,
    NeutronContext,
    TFTPContext,
    NginxContext,
    ObjectStoreContext,
    GlanceSwiftBackendContext)
from charmhelpers.fetch import (
    apt_update,
    apt_upgrade
)
import constants
import os
import subprocess
import urllib


def resource_map():
    resource_map = {
        constants.IRONIC_CONF: {
            'services': ['ironic-api', 'ironic-conductor'],
            'contexts': [context.LogLevelContext(),
                         context.SharedDBContext(
                             user=config('database-user'),
                             database=config('database'),
                             ssl_dir=constants.IRONIC_CONF_DIR),
                         context.ImageServiceContext(),
                         context.IdentityServiceContext(service='ironic',
                                                        service_user='ironic'),
                         NeutronContext(),
                         context.AMQPContext(
                             ssl_dir=constants.IRONIC_CONF_DIR),
                         IronicContext(),
                         NginxContext(),
                         ObjectStoreContext(),
                         GlanceSwiftBackendContext()],
        },
        constants.TFTP_CONF: {
            'services': [constants.TFTP_SERVICE_NAME],
            'contexts': [TFTPContext()]
        },
        constants.HTTPBOOT_AVAILABLE: {
            'services': [constants.NGINX_SERVICE_NAME],
            'contexts': [NginxContext()]
        },
        constants.PXELINUX_CONF: {
            'services': [],
            'contexts': [IronicContext()]
        }
    }

    return resource_map


def register_configs():
    '''
    Returns an OSTemplateRenderer object with all required configs registered.
    '''
    release = os_release('ironic-common')
    configs = templating.OSConfigRenderer(
        templates_dir=constants.TEMPLATES_DIR,
        openstack_release=release)

    for cfg, d in resource_map().iteritems():
        configs.register(cfg, d['contexts'])

    return configs


def restart_map():
    return {k: v['services'] for k, v in resource_map().iteritems()}


def services():
    ''' Returns a list of services associated with this charm '''
    _services = []
    for v in restart_map().values():
        _services = _services + v
    return list(set(_services))


def cmd_all_services(cmd):
    if cmd == 'start':
        for svc in services():
            if not service_running(svc):
                service_start(svc)
    else:
        for svc in services():
            service(cmd, svc)


def determine_ports():
    '''Assemble a list of API ports for the services'''
    ports = []
    for svc in services():
        if svc in constants.API_PORTS:
            ports.append(constants.API_PORTS[svc])
    return list(set(ports))


def migrate_ironic_database():
    log('Migrating Ironic database.')
    cmd = ['ironic-dbsync',
           '--config-file', constants.IRONIC_CONF,
           'upgrade']
    subprocess.check_output(cmd)


def chown(user=None, file_path=None, recusive=False):
    if not user or not file_path:
        return
    cmd = ['chown', '%s:%s' % (user, user), file_path]
    if recusive:
        cmd.append('-R')
    subprocess.check_output(cmd)


def copy_tftp_files(files_category, tftp_root):
    """This method is used to copy the necessary files expected by Ironic
       in the TFTP root directory. The 'constants.TFTP_FILES' directory
       is a mapping between the expected files paths (relative to TFTP root
       directory) and the source files paths. Depending on the 'files_category'
       passed as parameter, the necessary files are copied.
    """
    if files_category not in constants.TFTP_FILES:
        return
    log('Copying TFTP files for category %s' % files_category)
    for f_path, src_f_path in constants.TFTP_FILES[files_category].iteritems():
        target_f_path = os.path.join(tftp_root, f_path)
        urllib.urlretrieve(src_f_path, filename=target_f_path)


def set_up_pxe():
    """Configures the machine to be able to PXE boot Ironic nodes.
    """
    ironic_ctxt = IronicContext()()
    nginx_ctxt = NginxContext()()

    if not os.path.exists(ironic_ctxt['tftp_root']):
        os.mkdir(ironic_ctxt['tftp_root'])

    # Create directory so we can create the config file later
    if not os.path.exists(ironic_ctxt['pxelinux_cfg_root']):
        os.mkdir(ironic_ctxt['pxelinux_cfg_root'])

    copy_tftp_files('PXE', ironic_ctxt['tftp_root'])
    service_reload(constants.TFTP_SERVICE_NAME)

    if config('enable-ipxe'):
        copy_tftp_files('iPXE', ironic_ctxt['tftp_root'])
        if not os.path.exists(nginx_ctxt['http_root']):
            os.mkdir(nginx_ctxt['http_root'])
        chown(user=constants.IRONIC_USER,
              file_path=nginx_ctxt['http_root'],
              recusive=True)

        if os.path.islink(constants.DEFAULT_SITE_ENABLED):
            os.unlink(constants.DEFAULT_SITE_ENABLED)

        if not os.path.islink(constants.HTTPBOOT_ENABLED):
            os.symlink(constants.HTTPBOOT_AVAILABLE,
                       constants.HTTPBOOT_ENABLED)
        service_reload(constants.NGINX_SERVICE_NAME)

    else:
        if os.path.islink(constants.HTTPBOOT_ENABLED):
            os.unlink(constants.HTTPBOOT_ENABLED)
            service_reload(constants.NGINX_SERVICE_NAME)

    if config('enable-uefi'):
        if not os.path.exists(constants.GRUB_DIR):
            os.mkdir(constants.GRUB_DIR)
        copy_tftp_files('UEFI', ironic_ctxt['tftp_root'])

    chown(user=constants.IRONIC_USER,
          file_path=ironic_ctxt['tftp_root'],
          recusive=True)


def do_openstack_upgrade(configs):
    new_src = config('openstack-origin')
    new_os_rel = get_os_codename_install_source(new_src)

    log('Performing OpenStack upgrade to %s.' % (new_os_rel))

    configure_installation_source(new_src)
    dpkg_opts = [
        '--option', 'Dpkg::Options::=--force-confnew',
        '--option', 'Dpkg::Options::=--force-confdef',
    ]
    apt_update()
    apt_upgrade(options=dpkg_opts, fatal=True, dist=True)

    # set CONFIGS to load templates from new release
    configs.set_release(openstack_release=new_os_rel)
    configs.write_all()


def write_all_configs(configs):
    if config('enable-ipxe'):
        configs.write(constants.HTTPBOOT_AVAILABLE)
    configs.write(constants.IRONIC_CONF)
    configs.write(constants.TFTP_CONF)

    pxelinux_conf_dir = os.path.dirname(constants.PXELINUX_CONF)
    if not os.path.exists(pxelinux_conf_dir):
        os.makedirs(pxelinux_conf_dir)
    configs.write(constants.PXELINUX_CONF)
