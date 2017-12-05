## Overview

This charm deploys and configures a node with OpenStack Ironic which has 
integration with other OpenStack components.

## Configuration

Create an `options.yaml` file with the necessary configurations needed to deploy
the charm:

    ironic:
      series: xenial
      constraints: spaces=internal,public,baremetaldeploy,ipmimanagement
      num_units: 0
      annotations:
        "gui-x": "1353"
        "gui-y": "1078"
      options:
        openstack-origin: "cloud:xenial-newton"
        region: "RegionOne"
        enable-ipxe: False
        enabled-drivers: "pxe_ipmitool,agent_ipmitool"
        nodes-cleaning: False
        dhcp-provider: neutron
        debug: True
        verbose: True
        swift-url: "http://10.20.0.2:8787/"
        swift-account: "baremetal"
        swift-container: "images"
        swift-temp-url-duration: 1200
        swift-temp-url-key: "key"
        os-admin-network: "10.0.0.0/24"
        os-internal-network: "10.0.1.0/24"
        os-public-network: "10.0.2.0/24"
        os-deploy-network: "10.0.3.0/24"
        deploy-network-uuid: "7c3ee6a9-4f91-43d5-bb1c-44aea99abcf0"
        cleaning-network-uuid: "7c3ee6a9-4f91-43d5-bb1c-44aea99abcf0"


The above configurations can be used to deploy the charm using
the OpenStack Newton release. Make sure you change the config options according
to your needs. See the configuration section for details about the charm's config
options.

## Networking

OpenStack Ironic supports integration with Neutron, which is used as a DHCP
provider for the `ironic-conductor.`

## Usage

Deploy the charm and add the relations with the other OpenStack charms:

    juju deploy --config options.yaml ironic

    juju add-relation ironic mysql
    juju add-relation ironic keystone
    juju add-relation ironic rabbitmq-server
    juju add-relation ironic glance
    juju add-relation ironic neutron-api
    juju add-relation ironic swift-proxy

To scale out horizontally:

    juju add-unit ironic -n <number_of_units>

To scale down:

    juju destroy-unit ironic/<unit_number>


## To deploy locally

    $ juju deploy $path_to_this_checkout --series xenial
