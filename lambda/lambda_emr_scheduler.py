import boto3
import json
import os
import random

emr = boto3.client('emr')

STATES = ["Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut",
          "Delaware","DistrictofColumbia","Florida","Georgia","Hawaii","Idaho","Illinois",
          "Indiana","Iowa","Kansas","Kentucky","Louisiana","Maine","Maryland","Massachusetts",
          "Michigan","Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada",
          "NewHampshire","NewJersey","NewMexico","NewYork","NorthCarolina","NorthDakota",
          "Ohio","Oklahoma","Oregon","Pennsylvania","RhodeIsland","SouthCarolina","SouthDakota",
          "Tennessee","Texas","Utah","Vermont","Virginia","Washington","WestVirginia",
          "Wisconsin","Wyoming"]

def lambda_handler(event, context):
    jar_path = os.environ['JAR_PATH']
    state = random.choice(STATES)
    print("Launching converter for %s" % state)
    cluster = emr.run_job_flow(
        Name="OpenCity converter for %s" % state,
        ReleaseLabel='emr-5.28.0',
        VisibleToAllUsers=True,
        Applications=[{"Name": "Ganglia"}, {"Name": "Spark"}],
        ServiceRole='EMR_DefaultRole',
        JobFlowRole='EMR_EC2_DefaultRole',
        Configurations=[
            {
                'Classification': 'spark-hive-site',
                'Properties': {
                    'hive.metastore.client.factory.class': 'com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory'
                }
            },
            {
                'Classification': 'hive-site',
                'Properties': {
                    'hive.metastore.client.factory.class': 'com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory'
                }
            }
        ],
        Instances={
            'InstanceGroups': [
                {
                    'Name': 'Master instance group - 1',
                    'Market': 'SPOT',
                    'BidPrice': '0.2',
                    'InstanceRole': 'MASTER',
                    'InstanceType': 'm3.xlarge',
                    'InstanceCount': 1
                },
                {
                    'Name': 'Slave instance group - 1',
                    'Market': 'SPOT',
                    'BidPrice': '0.2',
                    'InstanceRole': 'CORE',
                    'InstanceType': 'm3.xlarge',
                    'InstanceCount': 4
                }
            ]
        },
        Steps=[
            {
                'Name': 'Convert %s' % state,
                'ActionOnFailure': 'TERMINATE_CLUSTER',
                'HadoopJarStep': {
                    'Jar': 'command-runner.jar',
                    'Args': [
                        'spark-submit',
                        '--deploy-mode', 'cluster',
                        '--conf', 'spark.sql.catalogImplementation=hive',
                        '--conf', 'spark.yarn.maxAppAttempts=1',
                        '--class', 'io.shuvalov.spark.kinesis.ingester.IngesterJob',
                        jar_path,
                        'select * from opencitymodel.jun2019 where state = "%s"' % state,
                        'OpenCity'
                    ]
                }
            }
        ]
    )
    print("Launched cluster %s" % cluster)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
