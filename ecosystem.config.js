module.exports = {
  apps: [
    {
      name: 'kafka-producer',
      script: 'kafka_pipeline/producer.py',
      cwd: '/home/ubuntu/Real-Time-Conversational-Intelligence-Platform',
      interpreter: 'python3',
      autorestart: false,
      env: {
        PYTHONPATH: '/home/ubuntu/Real-Time-Conversational-Intelligence-Platform:.'
      }
    },
    {
      name: 'pyspark-consumer',
      script: 'spark/spark_consumer.py',
      cwd: '/home/ubuntu/Real-Time-Conversational-Intelligence-Platform',
      interpreter: 'python3',
      env: {
        PYTHONPATH: '/home/ubuntu/Real-Time-Conversational-Intelligence-Platform:.'
      }
    }
  ]
};
