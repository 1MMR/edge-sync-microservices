from flask import Flask, jsonify
import shutil
import socket

app = Flask(__name__)

def check_disk(threshold_pct=90):
    total, used, free = shutil.disk_usage("/")
    pct = used / total * 100
    return pct < threshold_pct, {"percent_used": round(pct, 2)}

def check_network(host="1.1.1.1", port=53, timeout=3):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, {"checked_host": host, "port": port}
    except Exception as e:
        return False, {"error": str(e)}

@app.route('/healthz')
def healthz():
    disk_ok, disk_meta = check_disk()
    net_ok, net_meta = check_network()
    healthy = disk_ok and net_ok
    details = {"disk": disk_meta, "network": net_meta}
    status = 200 if healthy else 503
    return jsonify({"healthy": healthy, "details": details}), status

@app.route('/readyz')
def readyz():
    net_ok, net_meta = check_network()
    status = 200 if net_ok else 503
    return jsonify({"ready": net_ok, "network": net_meta}), status

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
