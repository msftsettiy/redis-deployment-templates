from rediscluster import RedisCluster
import os

# Define the cluster nodes
redis_port = os.getenv('REDIS_PORT', 6379)
startup_nodes = [{'host': '10.0.0.10', 'port': redis_port}, {'host': '10.0.0.11', 'port': redis_port}, {'host': '10.0.0.12', 'port': redis_port}]

print(f'Connecting to redis cluster using nodes: {startup_nodes} on port {redis_port}...')

# Initialize the RedisCluster client
rc = RedisCluster(decode_responses=True, startup_nodes=startup_nodes, skip_full_coverage_check=True, socket_connect_timeout=5, retry_on_timeout=True)
print('connected.')

# Set and get a key-value pair
rc.set("city", "San Fracisco")
rc.set("state", "CA")
rc.set("zip", "95630")

print(rc.get("state"))
print(rc.get("city"))
print(rc.get("zip"))