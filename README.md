# Instruction

Run Spark standalone:


```bash
$SPARK_HOME/sbin/start-all.sh
```

Submit job to spark:

```bash
spark-submit --packages org.apache.spark:spark-streaming-kafka-0-10_2.12:3.5.1,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,com.github.housepower:clickhouse-integration-spark_2.12:2.7.1,com.github.housepower:clickhouse-native-jdbc-shaded:2.7.1 streaming.py
```