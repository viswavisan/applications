import subprocess
import re
import json
import os
from flask import request, jsonify, render_template, redirect
from flask_smorest import Blueprint

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
static_dir = os.path.join(os.path.dirname(__file__), "static")

app = Blueprint('Monitor', __name__,
                template_folder=template_dir,
                static_folder=static_dir,
                static_url_path="/monitor/static",
                description="System monitoring dashboard and controls")


def get_services_memory():
    service_mem = []
    try:
        # Get current system services with their MemoryCurrent property
        cmd = "systemctl show '*.service' --property=Id,MemoryCurrent --no-pager"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            lines = res.stdout.strip().split('\n')
            current_mem = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('MemoryCurrent='):
                    val = line.split('=', 1)[1]
                    if val != '[not set]':
                        try:
                            current_mem = int(val)
                        except ValueError:
                            current_mem = None
                    else:
                        current_mem = None
                elif line.startswith('Id='):
                    unit = line.split('=', 1)[1].replace('.service', '')
                    if current_mem is not None and current_mem > 0:
                        service_mem.append({
                            "name": unit,
                            "memory": current_mem
                        })
                        current_mem = None
                        
            # Sort by memory descending
            service_mem.sort(key=lambda x: x["memory"], reverse=True)
    except Exception as e:
        pass
    return service_mem

def get_top_processes():
    proc_list = []
    try:
        # Get top 10 memory-consuming processes using ps
        cmd = "ps -eo pid,comm,rss --no-headers --sort=-rss"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            lines = res.stdout.strip().split('\n')
            for line in lines[:10]:
                parts = line.strip().split()
                if len(parts) >= 3:
                    pid = parts[0]
                    name = parts[1]
                    try:
                        rss_kb = int(parts[2])
                        memory_bytes = rss_kb * 1024
                        proc_list.append({
                            "pid": pid,
                            "name": name,
                            "memory": memory_bytes
                        })
                    except ValueError:
                        pass
    except Exception as e:
        pass
    return proc_list

# Views
@app.route('/monitor')
def index():
    return redirect('/services')

@app.route('/services')
def services_view():
    return render_template('services.html')

@app.route('/ports')
def ports_view():
    return render_template('ports.html')

@app.route('/memory')
def memory_view():
    return render_template('memory.html')

@app.route('/terminal')
def terminal_view():
    return render_template('terminal.html')


@app.route('/api/services', methods=['GET'])
def api_services():
    try:
        # Check systemd active services using JSON output format
        cmd = "systemctl list-units --type=service --state=running --output=json --no-pager"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        
        # Parse output JSON
        services = json.loads(result.stdout)
        
        formatted_services = []
        for s in services:
            formatted_services.append({
                "unit": s.get("unit", "unknown").replace(".service", ""),
                "load": s.get("load", "loaded"),
                "active": s.get("active", "active"),
                "sub": s.get("sub", "running"),
                "description": s.get("description", "")
            })
        return jsonify(formatted_services)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve services: {str(e)}"
        }), 500

@app.route('/api/services/control', methods=['POST'])
def control_service():
    try:
        data = request.get_json() or {}
        unit = data.get("unit")
        action = data.get("action") # 'stop' or 'restart'
        
        if not unit:
            return jsonify({
                "status": "error",
                "message": "Invalid service unit name."
            }), 400
            
        if action not in ('stop', 'restart'):
            return jsonify({
                "status": "error",
                "message": "Invalid action."
            }), 400
            
        # Standardize unit name (add .service if not present)
        service_name = unit if unit.endswith('.service') else f"{unit}.service"
        
        # Execute systemctl command using sudo
        cmd = f"echo radxa | sudo -S systemctl {action} {service_name}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "message": f"Successfully executed '{action}' on service '{service_name}'."
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to execute '{action}' on service: {result.stderr.strip()}"
            }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/ports', methods=['GET'])
def api_ports():
    try:
        # Try using sudo ss -tulpn first
        cmd = "echo radxa | sudo -S ss -tulpn"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # If it failed or output doesn't contain ports, try non-sudo ss -tuln
        if result.returncode != 0 or not result.stdout.strip():
            cmd = "ss -tuln"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
        lines = result.stdout.strip().split('\n')
        ports_list = []
        
        if len(lines) > 1:
            for line in lines[1:]:
                parts = re.split(r'\s+', line.strip())
                if len(parts) >= 5:
                    netid = parts[0]
                    state = parts[1]
                    local_addr_port = parts[4]
                    
                    # Extract process details if present
                    process_name = "N/A"
                    pid = "N/A"
                    
                    if len(parts) >= 7:
                        process_col = " ".join(parts[6:])
                        pid_match = re.search(r'pid=(\d+)', process_col)
                        name_match = re.search(r'"([^"]+)"', process_col)
                        if pid_match:
                            pid = pid_match.group(1)
                        if name_match:
                            process_name = name_match.group(1)
                            
                    # Separate address and port
                    if ':' in local_addr_port:
                        addr, port = local_addr_port.rsplit(':', 1)
                    else:
                        addr = local_addr_port
                        port = "unknown"
                        
                    # Standardize local host formats for display
                    if addr == "*":
                        addr = "0.0.0.0"
                    elif addr == "[::]":
                        addr = "::"
                        
                    ports_list.append({
                        "protocol": netid.upper(),
                        "state": state,
                        "local_address": addr,
                        "port": port,
                        "process": process_name,
                        "pid": pid
                    })
                    
        return jsonify(ports_list)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve ports: {str(e)}"
        }), 500

@app.route('/api/ports/kill', methods=['POST'])
def kill_port_process():
    try:
        data = request.get_json() or {}
        pid = data.get("pid")
        port = data.get("port")
        
        if not pid or pid == "N/A":
            return jsonify({
                "status": "error",
                "message": "Invalid PID provided."
            }), 400
            
        # Validate PID is numeric
        if not str(pid).isdigit():
            return jsonify({
                "status": "error",
                "message": "PID must be numeric."
            }), 400
            
        # Execute kill command using sudo
        cmd = f"echo radxa | sudo -S kill -9 {pid}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "message": f"Successfully terminated process with PID {pid} listening on port {port}."
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to kill process: {result.stderr.strip()}"
            }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/memory', methods=['GET'])
def api_memory():
    try:
        meminfo = {}
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split(':')
                if len(parts) == 2:
                    name = parts[0].strip()
                    val_str = parts[1].strip().split()[0]
                    meminfo[name] = int(val_str) * 1024 # convert to Bytes
                    
        total = meminfo.get('MemTotal', 0)
        free = meminfo.get('MemFree', 0)
        available = meminfo.get('MemAvailable', 0)
        buffers = meminfo.get('Buffers', 0)
        cached = meminfo.get('Cached', 0)
        
        # Calculate RAM usage
        if available > 0:
            used = total - available
        else:
            used = total - free - buffers - cached
            
        used_percent = round((used / total) * 100, 1) if total > 0 else 0
        
        # Swap usage
        swap_total = meminfo.get('SwapTotal', 0)
        swap_free = meminfo.get('SwapFree', 0)
        swap_used = swap_total - swap_free
        swap_percent = round((swap_used / swap_total) * 100, 1) if swap_total > 0 else 0
        
        # Service memory breakdown
        services_mem = get_services_memory()
        
        # Top processes memory breakdown
        processes_mem = get_top_processes()
        
        return jsonify({
            "ram": {
                "total": total,
                "used": used,
                "free": free,
                "available": available,
                "buffers_cached": buffers + cached,
                "used_percent": used_percent
            },
            "swap": {
                "total": swap_total,
                "used": swap_used,
                "free": swap_free,
                "used_percent": swap_percent
            },
            "services": services_mem,
            "processes": processes_mem
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve memory stats: {str(e)}"
        }), 500

@app.route('/api/terminal/execute', methods=['POST'])
def run_terminal_command():
    try:
        import os
        data = request.get_json() or {}
        command = data.get("command", "").strip()
        sudo_password = data.get("sudo_password", "").strip()
        
        if not command:
            return jsonify({
                "status": "error",
                "message": "Empty command."
            }), 400
            
        # Ensure askpass.sh helper script exists
        current_dir = os.path.dirname(os.path.abspath(__file__))
        askpass_path = os.path.join(current_dir, 'askpass.sh')
        if not os.path.exists(askpass_path):
            with open(askpass_path, 'w') as f:
                f.write('#!/bin/sh\necho "$SUDO_PASSWORD"\n')
            os.chmod(askpass_path, 0o755)

        # Set up environment variables for sudo -A
        env = os.environ.copy()
        env["SUDO_ASKPASS"] = askpass_path
        env["SUDO_PASSWORD"] = sudo_password

        # Define sudo wrapper function to use askpass (-A) in bash
        full_command = f"sudo() {{ /usr/bin/sudo -A \"$@\"; }}; export -f sudo; {command}"

        # Run command under subprocess with a 10s timeout using bash
        result = subprocess.run(
            ["/bin/bash", "-c", full_command],
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )
        
        return jsonify({
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({
            "status": "timeout",
            "message": "Command execution timed out (maximum 10 seconds limit reached)."
        }), 408
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/system/power', methods=['POST'])
def system_power():
    try:
        data = request.get_json() or {}
        action = data.get("action") # 'reboot' or 'shutdown'
        
        if action not in ('reboot', 'shutdown'):
            return jsonify({
                "status": "error",
                "message": "Invalid power action."
            }), 400
            
        # Select command
        if action == 'reboot':
            cmd = "echo radxa | sudo -S systemctl reboot"
        else:
            cmd = "echo radxa | sudo -S systemctl poweroff"
            
        # Run command asynchronously to allow the server to respond to the client
        import threading
        def run_power_cmd():
            import time
            time.sleep(1) # delay slightly to allow response to be sent
            subprocess.run(cmd, shell=True)
            
        threading.Thread(target=run_power_cmd).start()
        
        return jsonify({
            "status": "success",
            "message": f"System {action} initiated successfully. The dashboard will go offline shortly."
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    from flask import Flask
    standalone_app = Flask(__name__)
    standalone_app.secret_key = 'standalone_secret_key'
    
    @standalone_app.route('/')
    def standalone_index():
        return redirect('/services')
        
    from flask_smorest import Api
    api = Api(standalone_app)
    api.register_blueprint(app)
    
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    standalone_app.run(host='0.0.0.0', port=8000, debug=debug_mode)
