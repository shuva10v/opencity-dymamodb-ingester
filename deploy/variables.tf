variable "region" {
  type = string
  description = "AWS region"
}

variable "jar_path" {
  type = string
  description = "spark-kinesis-ingester Jar path"
}

variable "s3_static_bucket_name" {
  type = string
  description = "Name of the bucket with static content"
}

