module.exports = {
  apps: [
    {
      name: 'kafka-producer',
      script: 'kafka_pipeline/producer.py',
      interpreter: 'python3',
      autorestart: false,
      env: {
        PYTHONPATH: '.'
      }
    },
    {
      name: 'pyspark-consumer',
      script: 'spark/spark_consumer.py',
      interpreter: 'python3',
      env: {
        PYTHONPATH: '.'
      }
    }
  ]
};
