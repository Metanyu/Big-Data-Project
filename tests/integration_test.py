import time
import os
import sys
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement

def check_data():
    """
    Connects to Cassandra and checks if any data has been written to the 
    zone_performance_30m table. Retries for up to 60 seconds.
    """
    print("Connecting to Cassandra...")
    
    # Retry connection logic
    cluster = None
    session = None
    
    for i in range(10):
        try:
            cluster = Cluster(['localhost'], port=9042)
            session = cluster.connect('taxi_streaming')
            print("Connected to Cassandra!")
            break
        except Exception as e:
            print(f"Connection failed ({e}), retrying in 5s...")
            time.sleep(5)
            
    if not session:
        print("Could not connect to Cassandra after retries.")
        sys.exit(1)

    print("Polling for data in 'zone_performance_30m'...")
    
    # Poll for data
    timeout = 180
    start_time = time.time()
    
    query = "SELECT count(*) as cnt FROM zone_performance_30m"
    
    while time.time() - start_time < timeout:
        try:
            row = session.execute(query).one()
            count = row.cnt
            print(f"Current Row Count: {count}")
            
            if count > 0:
                print("SUCCESS: Data found in Cassandra!")
                sys.exit(0)
                
        except Exception as e:
            print(f"Query Error: {e}")
            
        time.sleep(2)
        
    print("TIMEOUT: No data appeared in Cassandra within 180 seconds.")
    sys.exit(1)

if __name__ == "__main__":
    check_data()
