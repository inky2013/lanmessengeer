import log
import base
import argparse
logger = log.setup_logger('root')

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=8000)
parser.add_argument('--window-title', type=str, default="Lan Messenger")
parser.add_argument('--dev-tools', type=bool, default=False)
parser.add_argument('--chunk-length', type=int, default=53)
parser.add_argument('--encrypted', type=bool, default=False)
args = parser.parse_args()

ui = base.UIInfo("MyName", port=args.port, window_name=args.window_title, dev_tools=args.dev_tools, rsa_c_len=args.chunk_length, encrypt_messages=args.encrypted)
