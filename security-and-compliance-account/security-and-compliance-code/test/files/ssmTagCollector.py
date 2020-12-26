import json
import boto3
import logging
import os

#setup simple logging for INFO
logger = logging.getLogger()
logger.setLevel(logging.INFO)

CentralAccountRegion = os.environ.get('CentralAccountRegion')
CentralAccountId = os.environ.get('CentralAccountId')

#define the connection region
ec2 = boto3.resource('ec2')
lambdaClient = boto3.client('lambda',region_name=CentralAccountRegion)

filters = [
              {
                  'Name': 'instance-state-name',
                  'Values': ['running', 'stopped']
              },
              {
                  'Name': 'tag-key',
                  'Values': ['managedinstanceid']
              }
          ]

def lambda_handler(event, context):
    base = ec2.instances.filter(Filters=filters)
    eventData = {"instances":[]}
    eventDataInstances = eventData['instances']
    #loop through instances and create a collection
    for instance in base:
        logger.info ( "Reporting tag data for " + instance.id )
        # check to see if the instance has tags before trying this
        if instance.tags is not None:
            for tag in instance.tags:
                if tag['Key'] == 'managedinstanceid':
                    managedInstanceId = tag['Value']
                    logger.info( "Found managed instance id " + managedInstanceId + " with " + str( instance.tags ) )
                    eventDataInstances.append( { "instanceId": managedInstanceId, "tags": instance.tags })

    logger.info( "Ready to send data to SSM Tagger: " + str(eventData) )

    response = lambdaClient.invoke(
        FunctionName="arn:aws:lambda:" + CentralAccountRegion + ":" + CentralAccountId + ":function:ssm-tag-manager",
        InvocationType='Event',
        Payload=json.dumps(eventData)
        )
