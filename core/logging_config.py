import logging
import json
import sys
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)
        return json.dumps(log_entry)

def setup_logging(log_level=logging.INFO, json_output=True, log_file="everestkush.log"):
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(JSONFormatter() if json_output else logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(console)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    return root_logger
