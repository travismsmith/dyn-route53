#!/usr/bin/env python3
import logging
import os
import urllib.request

from configparser import ConfigParser
from pathlib import Path

import boto3

logging.basicConfig(filename='/var/log/dyn.log',format='%(asctime)s - %(message)s',level=logging.WARNING)

record = os.environ['Record_Name']
zone   = os.environ['Record_Zone']

publicIp = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')

credentialsFile = '{}/.aws/credentials'.format(str(Path.home()))

config = ConfigParser()
config.read(credentialsFile)

iam = boto3.client('iam')
route53 = boto3.client('route53')
sts = boto3.client('sts')

currentIp = route53.test_dns_answer(
    HostedZoneId=zone,
    RecordName=record,
    RecordType='A'
)['RecordData'][0]

if currentIp != publicIp:
  logging.warning('Old Value: {} = {}'.format(record, currentIp))
  logging.warning('New Value: {} = {}'.format(record, publicIp))
  response = route53.change_resource_record_sets(
    HostedZoneId=zone,
    ChangeBatch={
      'Changes': [
        {
          'Action': 'UPSERT',
          'ResourceRecordSet': {
            'Name': record,
            'Type': 'A',
            'TTL': 300,
            'ResourceRecords': [
              {
                'Value': publicIp
              },
            ]
          }
        },
      ]
    }
  )


# Get current user info
response = sts.get_caller_identity()
user = response['Arn'].split('/')[1]
accessKey = config.get('default', 'AWS_ACCESS_KEY_ID')

response = iam.create_access_key(UserName=user)

# Write the new Key Pair to disk
config.set('default', 'AWS_ACCESS_KEY_ID', response['AccessKey']['AccessKeyId'])
config.set('default', 'AWS_SECRET_ACCESS_KEY', response['AccessKey']['SecretAccessKey'])
with open(credentialsFile, 'w') as configfile:
    config.write(configfile)

# Delete Old Access key
deleteResponse = iam.delete_access_key(
    UserName=user,
    AccessKeyId=accessKey
)
