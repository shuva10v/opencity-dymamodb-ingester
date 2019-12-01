package io.shuvalov.spark.kinesis.ingester

import scala.util.parsing.json.JSONObject
import com.amazonaws.services.kinesis.AmazonKinesisClient
import com.amazonaws.services.kinesis.model.PutRecordRequest
import java.nio.ByteBuffer
import org.apache.spark.sql.DataFrame
import org.apache.spark.sql.Row
import org.apache.spark.sql.SparkSession

object IngesterJob {
	def ingest(source: DataFrame, streamName: String)(implicit spark: SparkSession): Unit = {
		import spark.implicits._
		val pushToKinesis = source.mapPartitions{iter => 
	    	val kinesisClient = new AmazonKinesisClient()
	    	kinesisClient.setEndpoint("https://kinesis.eu-west-1.amazonaws.com")
		    iter.map{ obj =>
		        val put = new PutRecordRequest()
		        put.setStreamName(streamName)
		        put.setPartitionKey(obj.getAs[String]("hash"))
		        val m = obj.getValuesMap(obj.schema.fieldNames)
		        val raw = JSONObject(m).toString()
		        put.withData(ByteBuffer.wrap(raw.getBytes()))
		        val putRecordResult = kinesisClient.putRecord(put)
		        putRecordResult.getSequenceNumber()
		    }
		}
		pushToKinesis.count // materialize lazy ops
	}
	def main(args: Array[String]): Unit = {
		implicit val spark: SparkSession = SparkSession.builder().appName(getClass.getSimpleName).getOrCreate()
		import spark.implicits._
		args match {
			case Array(sql, streamName) =>
				val source = spark.sql(sql)
				ingest(source, streamName)
			case _ =>
				 throw new IllegalArgumentException("Error input arguments format " + args)
		}
	}
}
