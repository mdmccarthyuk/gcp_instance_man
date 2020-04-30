"""
A tool to create and manage instances with a data disk attached from
a snapshot and to take new snapshots on instance shutdown with a hope
of saving me some money :)
"""

import sys
from googleapiclient import discovery
from google.oauth2 import service_account
import argparse


def list_instances(project, zone, auth_file):
    # Lists instances and show any disks that are attached beyond the bootable disk
    credentials = service_account.Credentials.from_service_account_file(auth_file)
    compute = discovery.build('compute', 'v1', credentials=credentials)
    instances = compute.instances().list(project=project, zone=zone).execute()
    for i in instances['items']:
        print(i['name'])
        for d in i['disks']:
            # Only show disks that aren't bootable
            if not d['boot']:
                print("  " + str(d['deviceName']))
    return 0


def snapshot_disk(project, zone, auth_file, instance, disk):
    # Creates a snapshot of the named disk on the named instance
    credentials = service_account.Credentials.from_service_account_file(auth_file)
    compute = discovery.build('compute', 'v1', credentials=credentials)
    instances = compute.instances().list(project=project, zone=zone).execute()
    for i in instances['items']:
        if i['name'] == instance:
            for d in i['disks']:
                if d['deviceName'] == disk:
                    if d['boot']:
                        print("ERROR: That disk is bootable")
                        sys.exit(1)
                    else:
                        print("Snapshotting")
                        region = zone[0:len(zone)-2]
                        snapshot_body = {
                            "name": disk+"-001",
                            "storageLocations": [region]
                        }
                        request = compute.disks().createSnapshot(project=project, zone=zone, disk=disk,
                                                                 body=snapshot_body)
                        response = request.execute()
                        print(response)
                        sys.exit(0)
    print("ERROR: Matching disk not found")
    sys.exit(1)


def list_snapshots(project, zone, auth_file):
    # Displays a list of snapshots
    credentials = service_account.Credentials.from_service_account_file(auth_file)
    compute = discovery.build('compute', 'v1', credentials=credentials)
    snapshots = compute.snapshots().list(project=project).execute()
    for s in snapshots['items']:
        print(s['name'] + " - " + s['creationTimestamp'] + " - " + s['diskSizeGb'] + " Gb")
    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--project', help='The Project ID', required=True)
    parser.add_argument('--zone', help='The compute engine zone to use', required=True)
    parser.add_argument('--auth', help='Path to the service auth json file', required=True)

    subparsers = parser.add_subparsers(dest='command', required=True)

    list_instances_parser = subparsers.add_parser('list_instances')

    snapshot_disk_parser = subparsers.add_parser('snapshot_disk')
    snapshot_disk_parser.add_argument('--instance')
    snapshot_disk_parser.add_argument('--disk')

    list_snapshots_parser = subparsers.add_parser('list_snapshots')

    args = parser.parse_args()

    if args.command == 'list_instances':
        list_instances(args.project, args.zone, args.auth)
    elif args.command == 'snapshot_disk':
        snapshot_disk(args.project, args.zone, args.auth, args.instance, args.disk)
    elif args.command == 'list_snapshots':
        list_snapshots(args.project, args.zone, args.auth)

    sys.exit(0)
