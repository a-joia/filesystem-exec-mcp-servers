import subprocess
import yaml
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

scripts = config.get('scripts', [])

for script in scripts:
    script_path = os.path.join(os.path.dirname(__file__), script)
    print(f'Running {script_path}...')
    result = subprocess.run(['python', script_path], capture_output=True, text=True, cwd=PROJECT_ROOT)
    print(result.stdout)
    if result.returncode != 0:
        print(f'FAILED: {script_path}')
        print(result.stderr)
    else:
        print(f'PASSED: {script_path}') 