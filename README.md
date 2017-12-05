## Overview

This charm deploys and configures a node with OpenStack Ironic which has 
integration with other OpenStack components. Services from the node are: 
`ironic-api`, `ironic-conductor`, `tftpd-hpa` and optionally `nginx`.

Nginx is optionally used as a light-weight web server used to serve
iPXE files over http, in case the charm is configured to use iPXE instead of
traditional PXE.

## Configuration

Create an `options.yaml` file with the necessary configurations needed to deploy
the charm:

    ironic:
      openstack-origin: "cloud:xenial-newton"
      enable-ipxe: True
      enabled-drivers: "pxe_ipmitool,agent_ipmitool"
      nodes-cleaning: False

The above configurations can be used to deploy the charm using
the OpenStack Newton release. You may change the config options according to your
needs. See the configuration section for details about the charm's config
options.

## Networking

OpenStack Ironic supports integration with Neutron, which is used as a DHCP
provider for the `ironic-conductor.`

As a requirement, prior to deploying the charm, you'll have to configure the
`neutron-gateway` node with a flat network provider that uses a NIC which is
connected to an isolated network dedicated for Ironic traffic.

When iPXE is enabled, DHCP requests from iPXE need to have a DHCP tag called
"ipxe", in order for the DHCP server to tell the client to get the "boot.ipxe"
script via HTTP. Thus, you must configure `neutron-gateway` units accordingly:

    juju set neutron-gateway dnsmasq-flags="dhcp-userclass=set:ipxe,iPXE, dhcp-match=set:ipxe,175"

## Usage

Deploy the charm and add the relations with the other OpenStack charms:

    juju deploy --config options.yaml cs:~cloudbaseit/xenial/ironic
    juju add-relation ironic mysql
    juju add-relation ironic keystone
    juju add-relation ironic rabbitmq-server
    juju add-relation ironic glance
    juju add-relation ironic neutron-api
    juju add-relation ironic nova-compute-ironic

To scale out horizontally:

    juju add-unit ironic -n <number_of_units>

To scale down:

    juju destroy-unit ironic/<unit_number>


## To deploy locally

    $ juju deploy $path_to_this_checkout --series xenial