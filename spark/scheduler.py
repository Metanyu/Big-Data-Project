import os
import time
import subprocess
import logging
import sys
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("batch_scheduler")

SPARK_JARS = (
    "/opt/spark-jars/spark-sql-kafka-0-10_2.12-3.5.1.jar,"
    "/opt/spark-jars/kafka-clients-3.4.1.jar,"
    "/opt/spark-jars/spark-token-provider-kafka-0-10_2.12-3.5.1.jar,"
    "/opt/spark-jars/commons-pool2-2.11.1.jar,"
    "/opt/spark-jars/spark-cassandra-connector-assembly_2.12-3.5.1.jar"
)

SUBMIT_CMD = [
    "/opt/spark/bin/spark-submit",
    "--master", "local[*]",
    "--jars", SPARK_JARS,
    "--conf", "spark.sql.streaming.checkpointLocation=/tmp/spark_checkpoints_batch", 
    "/opt/spark-apps/streaming.py",
    "--mode", "batch"
]

def get_args():
    parser = argparse.ArgumentParser(description="Spark Batch Job Scheduler")
    parser.add_argument("--speedup", type=float, default=3600.0, help="Simulation speedup factor")
    return parser.parse_args()

def run_batch_job():
    logger.info(">>> Triggering Daily Batch Job...")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            SUBMIT_CMD,
            capture_output=True,
            text=True
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"Batch Job Completed Successfully in {duration:.2f}s.")
        else:
            logger.error(f"Batch Job Failed after {duration:.2f}s!")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            
    except Exception as e:
        logger.error(f"Failed to execute subprocess: {e}")

def main():
    args = get_args()
    
    real_seconds_per_sim_day = 86400.0 / args.speedup
    
    logger.info("--- Spark Batch Scheduler Service Started ---")
    logger.info(f"Simulation Speedup: {args.speedup}x")
    logger.info(f"Schedule: Running every {real_seconds_per_sim_day:.2f} seconds (Simulated Day)")
    
    while True:
        run_batch_job()
        
        logger.info(f"Waiting {real_seconds_per_sim_day:.2f}s until next run...")
        time.sleep(real_seconds_per_sim_day)

if __name__ == "__main__":
    main()
