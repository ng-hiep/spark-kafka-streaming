from pyspark.sql import SparkSession
from pyspark.sql.types import StringType, StructField, StructType, IntegerType
from pyspark.sql.functions import from_json,current_timestamp
import os
from dotenv import load_dotenv

load_dotenv()

CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST')
CLICKHOUSE_PORT = os.getenv('CLICKHOUSE_PORT')
CLICKHOUSE_USER = os.getenv('CLICKHOUSE_USER')
CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD')

KAFKA_HOST = os.getenv('KAFKA_HOST')
KAFKA_BROKER1_PORT = os.getenv('KAFKA_BROKER1_PORT')
KAFKA_BROKER2_PORT = os.getenv('KAFKA_BROKER2_PORT')
KAFKA_BROKER3_PORT = os.getenv('KAFKA_BROKER3_PORT')


json_schema = StructType([
    StructField('sslsni', StringType(), True),
    StructField('subscriberid', StringType(), True),
    StructField('hour_key', IntegerType(), True),
    StructField('count', IntegerType(), True),
    StructField('up', IntegerType(), True),
    StructField('down', IntegerType(), True)
])


spark = SparkSession.builder \
    .appName("Streaming from Kafka") \
    .config("spark.streaming.stopGracefullyOnShutdown", True) \
    .config('spark.jars.packages', 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1') \
    .config("spark.sql.shuffle.partitions", 4) \
    .master("spark://deptrai:7077") \
    .getOrCreate()


df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", f"{KAFKA_HOST}:{KAFKA_BROKER1_PORT},{KAFKA_HOST}:{KAFKA_BROKER2_PORT},{KAFKA_HOST}:{KAFKA_BROKER3_PORT}") \
    .option("failOnDataLoss", "false") \
    .option("subscribe", "test-url-1204") \
    .load()
    
json_df = df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING) as msg_value")
json_expanded_df = json_df.withColumn("msg_value", from_json(json_df["msg_value"], json_schema)).select("msg_value.*")
exploded_df = json_expanded_df.select("sslsni", "subscriberid", "hour_key", "count", "up", "down") 
df_with_date = exploded_df.withColumn("inserted_time", current_timestamp())


def foreach_batch_function(df, epoch_id):
    df.write \
        .format("jdbc") \
        .mode("append") \
        .option("driver", "com.github.housepower.jdbc.ClickHouseDriver") \
        .option("url", "jdbc:clickhouse://" + CLICKHOUSE_HOST + ":" + CLICKHOUSE_PORT) \
        .option("user", CLICKHOUSE_USER) \
        .option("password", CLICKHOUSE_PASSWORD) \
        .option("dbtable", "default.raw_url") \
        .save()

writing_df = df_with_date \
    .writeStream \
    .foreachBatch(foreach_batch_function) \
    .start()

writing_df.awaitTermination()