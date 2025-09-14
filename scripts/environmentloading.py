# _script/faronix_env.py
import sys
import os
from pathlib import Path
from dotenv import load_dotenv # type: ignore

load_dotenv()
ROOT = os.getenv('FARONIX_ROOT')
CONFIG = os.getenv('CONFIG')
LOADSCRIPTS = Path(ROOT, CONFIG)
sys.path.insert(0, str(LOADSCRIPTS))




def fenv():
    
    """
    Load environment variables from _config.py and return as a dictionary.
    """

    env = {
        "FARONIX_ROOT": str(os.getenv('FARONIX_ROOT')),
        "SYSCONF": str(os.getenv('SYSCONF')),
        "MANIFEST": str(os.getenv('MANIFEST')),
        "BUILDER": str(os.getenv('BUILDER')),
        "RUNTIME": str(os.getenv('RUNTIME')),
        "DOCKER": str(os.getenv('DOCKER')),
        "NGINX": str(os.getenv('NGINX')),
        "SYSTEMD": str(os.getenv('SYSTEMD')),
        "SCRIPTS": str(os.getenv('SCRIPTS')),
        "LOG_FILE": str(os.getenv('LOG_FILE')),
        "ENDPOINT": str(os.getenv('ENDPOINT')),
        "ENV_FILE": str(os.getenv('ENV_FILE')),
    }


    for k, v in env.items():
        os.environ[k] = v