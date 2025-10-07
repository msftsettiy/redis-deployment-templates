# frontend.py
from flask import Flask, jsonify, request
from rediscluster import RedisCluster

from azure.confidentialledger import (
    ConfidentialLedgerClient, 
    ConfidentialLedgerCertificateCredential
)

from azure.confidentialledger.certificate import (
    ConfidentialLedgerCertificateClient,
)

from azure.core.exceptions import HttpResponseError

import os
import uuid
import tempfile
import json

app = Flask(__name__)

# Connect to Redis
redis_port = os.getenv('REDIS_PORT', 6379)
startup_nodes = [{'host': '10.0.0.10', 'port': redis_port}, {'host': '10.0.0.11', 'port': redis_port}, {'host': '10.0.0.12', 'port': redis_port}]

# Connect to Azure Confidential Ledger
admin_cert = open('/app/certs/admin_cert.pem', 'r').read()
admin_privk = open('/app/certs/admin_privk.pem', 'r').read()

USER_CERTIFICATE = f"{admin_cert}\n{admin_privk}"

ledger_name = os.getenv('LEDGER_NAME', 'settiy-redis-test1')
identity_url = "https://identity.confidential-ledger.core.azure.com"
ledger_url = f"https://{ledger_name}.confidential-ledger.azure.com"

print(f'Creating a ledger client for: {ledger_url}...')
identity_client = ConfidentialLedgerCertificateClient(identity_url)
network_identity = identity_client.get_ledger_identity(
     ledger_id=ledger_name
)

ledger_tls_cert_file_name = "networkcert.pem"
with open(ledger_tls_cert_file_name, "w") as cert_file:
    cert_file.write(network_identity['ledgerTlsCertificate'])

with tempfile.NamedTemporaryFile(
        "w", suffix=".pem", delete=False
    ) as user_cert_file:
        user_cert_file.write(USER_CERTIFICATE)
        user_certificate_path = user_cert_file.name
    
ledger_client = ConfidentialLedgerClient(
    endpoint=ledger_url, 
    credential=ConfidentialLedgerCertificateCredential(
       certificate_path=user_cert_file.name,
    ),
    ledger_certificate_path=ledger_tls_cert_file_name
)

print('done.')

print(f'Connecting to redis cluster using nodes: {startup_nodes} on port {redis_port}...')

# Initialize the RedisCluster client
rc = RedisCluster(decode_responses=True, startup_nodes=startup_nodes, skip_full_coverage_check=True, socket_connect_timeout=5, retry_on_timeout=True)

print('done.')

# CREATE: Writ to ledger and cache
@app.route('/ledger/<collectionid>', methods=['POST'])
def create_cache(collectionid):
    try:
        value = request.json.get('value')
    
        # Write the entry to the ledger
        print(f'Writing entry to ledger: {value} with collection {collectionid}...')
        post_entry_result = ledger_client.create_ledger_entry(  # type: ignore[attr-defined]
            {"contents": f"{value}"},
            collection_id=collectionid
        )
        
        transaction_id = post_entry_result["transactionId"]

        print(f"The new ledger entry has been committed successfully at Tx ID {transaction_id}")
        
        key = str(uuid.uuid1())
        value = json.dumps({"transaction_id": transaction_id, "collection_id": collectionid})
        
        rc.set(key, value)
        print(f'Set {key} with transaction id {transaction_id} and collection id {collectionid} in cache.')
            
        return jsonify({"message": key}), 201
    except HttpResponseError as e:
        print("Request failed: {}".format(e.response.json()))  # type: ignore[union-attr]
        return jsonify({"message": "Request failed"}), 500

# READ: Do a key exchange.
@app.route('/ledger/<key>', methods=['GET'])
def get_cache(key):
    if rc.exists(key):
        try:
            value = rc.get(key)
            return jsonify({"key": key, "value": value}), 200
        except HttpResponseError as e:
            print("Request failed: {}".format(e.response.json()))  # type: ignore[union-attr]
            return jsonify({"message": "Request failed"}), 500
    else:        
        return jsonify({"message": "Key not found"}), 404

@app.route('/health_check', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
