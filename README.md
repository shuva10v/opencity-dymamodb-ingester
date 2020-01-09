# OpenCity DynamoDB uploader

The project uploads [Open City Model database](https://github.com/opencitymodel/opencitymodel) to DynamoDB with EMR, Kinesis and Lambda.

How it works:

1. EMR cluster launched every N hours. The only step it has - Spark job [spark-kinesis-ingester](./spark-kinesis-ingester/).
2. [spark-kinesis-ingester](./spark-kinesis-ingester/) reads data from S3 Data Lake (tables metadata comes from Glue Data Catalog)
and puts it into Kinesis stream. [Open City Model](https://github.com/opencitymodel/opencitymodel) data partitioned by US states
 and on each invocation one random US state data processed.
3. Lambda function [OpenCityDDBWriter](./lambda/lambda_ddb_writer.py) reads records from the Kinesis stream and puts it into DynamoDB table.
4. Web application for navigating OpenCity data build with Lambda and API Gateway.  

Overall architecture: 

![](./architecture.png)

# Deployment

1. Create Glue table as described [here](https://github.com/opencitymodel/opencitymodel/blob/master/examples/Query-OpenCityModel-using-AWS-Athena.md)

2. Build [spark-kinesis-ingester](./spark-kinesis-ingester/) module:

````
mvn clean install
````

3. Put jar `/target/spark-kinesis-ingester-1.0-SNAPSHOT.jar` to your S3 bucket.

4. Go to [deploy](./deploy) folder and prepare terraform config file `config.tfvars`:

````
region="es-east-1"
jar_path="s3://your_bucket/jars/spark-kinesis-ingester-1.0-SNAPSHOT.jar"
s3_static_bucket_name="static-content-bucket"
````

5. Go to [webapp](./webapp) folder and build frontend:

```
npm install
gulp
```

6. Apply it:

````
terraform init
terraform plan -var-file=config.tfvars
terraform apply -var-file=config.tfvars
````             

It outputs API Gateway endpoint:
````
Outputs:

backend_api_url = https://???????.execute-api.eu-west-1.amazonaws.com/opencity
````             

7.  Go to [webapp](./webapp) folder and build frontend with api url from the previous step:
    
```
gulp --api_endpoint https://???????.execute-api.eu-west-1.amazonaws.com/opencity
```                                                                             

8. Apply terraform one more time:

````
terraform apply -var-file=config.tfvars
````                  

# Init OSM data

To init OSM data:

1. Run CMR cluster

2. Create `planet` table as described [here](https://aws.amazon.com/blogs/big-data/querying-openstreetmap-with-amazon-athena/)

3. Run Job with:

````
spark-submit 
--deploy-mode cluster 
--conf spark.sql.catalogImplementation=hive 
--conf spark.yarn.maxAppAttempts=1 
--class io.shuvalov.spark.kinesis.ingester.IngesterJob 
%jar_path%
"SELECT concat('', id) as hash, type, to_json(tags) as tags, lat, lon, to_json(nds) as nds, to_json(members) as members, 
unix_timestamp(timestamp) as timestamp, uid, user, version FROM opencitymodel.planet limit 10" 
OSM
````


