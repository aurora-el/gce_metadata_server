from os import environ
from ipaddress import ip_network
from google.cloud import compute_v1
from directory import Directory

class Config:
    def __init__(self):
        self.INSTANCE_NAME = environ.get('GCE_INSTANCE')
        self.PROJECT_NAME = environ.get('GCE_PROJECT')
        self.ZONE = environ.get('GCE_ZONE')
        self.get_project()
        self.get_instance()

    APPLICATION_ROOT = '/computeMetadata/v1/'

    PROJECT = {}

    def get_project(self):
        # project endpoint
        project_data = compute_v1.ProjectsClient().get(request={
            'project': self.PROJECT_NAME})

        self.PROJECT = Directory({
            'project-id': self.PROJECT_NAME,
            'numeric-project-id': project_data.id,
            'attributes': Directory({item.key: item.value for item in project_data.common_instance_metadata.items}),
        })

    INSTANCE = {}

    def get_instance(self):
        # instance endpoint
        instance_data = compute_v1.InstancesClient().get(request={
            'project': self.PROJECT_NAME,
            'zone': self.ZONE,
            'instance': self.INSTANCE_NAME})
        disk_data = compute_v1.DisksClient().get(request={
            'project': self.PROJECT_NAME,
            'zone': self.ZONE,
            'disk': next(disk.source for disk in instance_data.disks if disk.boot).split('/')[-1]})
        subnet_client = compute_v1.SubnetworksClient()
        subnets_data = {interface.name: subnet_client.get(request={
            'project': self.PROJECT_NAME,
            'region': interface.subnetwork.split('/')[-3],
            'subnetwork': interface.subnetwork.split('/')[-1]})
            for interface in instance_data.network_interfaces}

        self.INSTANCE = Directory({
            'name': self.INSTANCE_NAME,
            'id': instance_data.id,
            'description': instance_data.description,
            'attributes': Directory({item.key: item.value for item in instance_data.metadata.items}),
            'zone': self.ZONE,
            'machine-type': instance_data.machine_type.removeprefix('https://www.googleapis.com/compute/v1'),
            'cpu-platform': instance_data.cpu_platform,
            'disks': Directory([{
                'device-name': disk.device_name,
                'index': disk.index,
                'interface': disk.interface,
                'mode': disk.mode,
                'type': disk.type_,
            } for disk in instance_data.disks]),
            'image': disk_data.source_image.removeprefix('https://www.googleapis.com/compute/v1'),
            'licenses': Directory([license_.removeprefix('https://www.googleapis.com/compute/v1')
                                   for disk in instance_data.disks for license_ in disk.licenses]),  # could be wrong?
            'service-accounts': Directory([{
                'email': sa.email,
                'scopes': [scope for scope in sa.scopes]}
                for sa in instance_data.service_accounts]),  # without tokens
            'hostname': instance_data.hostname,
            'network-interfaces': Directory([{
                'access-configs': Directory([{
                    'external-ip': access_config.nat_i_p or access_config.external_ipv6,
                    'type': access_config.type_,
                } for access_config in interface.access_configs]),
                'gateway': subnets_data[interface.name].gateway_address,
                'ip': interface.network_i_p,
                'network': interface.network.split('/')[-1],
                'subnetmask': ip_network(subnets_data[interface.name].ip_cidr_range).netmask,
            } for interface in instance_data.network_interfaces]),
            'tags': [tag for tag in instance_data.tags.items],
            'scheduling': Directory({
                'on-host-maintenance': instance_data.scheduling.on_host_maintenance,
                'automatic-restart': instance_data.scheduling.automatic_restart,
                'preemptible': instance_data.scheduling.preemptible,
            }),
            'legacy-endpoint-access': Directory(['0.1', 'v1beta1'])
        })


