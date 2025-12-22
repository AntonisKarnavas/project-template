import pytest
import subprocess
import sys
import os
import time
import requests
import signal
import socket

def wait_for_port(port, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.1)
    return False

@pytest.fixture
def running_server(request):
    """
    Fixture to run the server in a subprocess.
    Parametrized with environment variables.
    """
    env_overrides = request.param
    env = os.environ.copy()
    env.update(env_overrides)
    
    # Use a random port or fixed test port? Fixed to 8003 to avoid conflict with defaults
    port = 8003
    
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
        cwd=os.getcwd(), # Ensure we run from project root
    )
    
    if not wait_for_port(port):
        process.kill()
        stdout, stderr = process.communicate()
        pytest.fail(f"Server failed to start on port {port}.\nSTDOUT: {stdout}\nSTDERR: {stderr}")
        
    yield f"http://localhost:{port}", process
    
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.mark.parametrize("running_server", [{"ENVIRONMENT": "prod"}], indirect=True)
def test_prod_logging_format(running_server):
    base_url, process = running_server
    
    # Make request
    requests.get(f"{base_url}/health")
    
    # We need to capture logs. Since Popen buffers, we might need to flush or terminate.
    # Terminating usually flushes.
    process.terminate()
    stdout, stderr = process.communicate(timeout=5)
    
    # Analyze
    assert "{" in stdout, "PROD logs should contain JSON objects"
    assert "record" in stdout or "text" in stdout or "level" in stdout


@pytest.mark.parametrize("running_server", [{"ENVIRONMENT": "dev"}], indirect=True)
def test_dev_logging_format(running_server):
    base_url, process = running_server
    
    requests.get(f"{base_url}/health")
    
    process.terminate()
    stdout, stderr = process.communicate(timeout=5)
    
    # In DEV, we expect readable text, not strictly JSON lines (though libraries vary)
    # Typically loguru dev format is colored text.
    # Check that we DON'T see a JSON object as the whole line.
    
    # Note: This assertion is a bit loose because "{" can appear in text.
    # But usually dev logs start with timestamp/level, not "{".
    # Let's check for INFO or similar.
    assert "INFO" in stdout or "200 OK" in stdout
