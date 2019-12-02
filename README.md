# OpenCity DynamoDB uploader

The project uploads [Open City Model database](https://github.com/opencitymodel/opencitymodel) to DynamoDB with EMR, Kinesis and Lambda.

How it works:

1. EMR cluster launched every N hours. The only step it has - Spark job [spark-kinesis-ingester](./spark-kinesis-ingester/).
2. [spark-kinesis-ingester](./spark-kinesis-ingester/) reads data from S3 Data Lake (tables metadata comes from Glue Data Catalog)
and puts it into Kinesis stream. [Open City Model](https://github.com/opencitymodel/opencitymodel) data partitioned by US states
 and on each invocation one random US state data processed.
3. Lambda function [OpenCityDDBWriter](./lambda/lambda_ddb_writer.py) reads records from the Kinesis stream and puts it into DynamoDB table.  

Overall architecture: 

![](./architecture.png)

# Deployment

1. Create Glue table as described [here](https://github.com/opencitymodel/opencitymodel/blob/master/examples/Query-OpenCityModel-using-AWS-Athena.md)

2. Build [spark-kinesis-ingester](./spark-kinesis-ingester/) module:

````
mvn clean install
````

3. Put jar `/target/spark-kinesis-ingester-1.0-SNAPSHOT.jar` to your S3 bucket.

4. Prepare terraform config file `config.tfvars`:

````
region="es-east-1"
jar_path="s3://your_bucket/jars/spark-kinesis-ingester-1.0-SNAPSHOT.jar"
````

5. Apply it:

````
terraform init
terraform plan -var-file=config.tfvars
terraform apply -var-file=config.tfvars
````

