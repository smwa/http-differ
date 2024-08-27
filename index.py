import sys
import time
import argparse
from typing import List
import sys
import traceback

import requests
import yaml
from Levenshtein import distance

argparser = argparse.ArgumentParser()
argparser.add_argument('config_file', type=str, help='A required location of a .yml config file, see example in repository')
args = argparser.parse_args()

class EndpointConfiguration():
  def __init__(self, name: str, url: str, interval: int, percent_diff_limit: float):
    self.name = name
    self.url = url
    self.interval = interval
    self.percent_diff_limit = percent_diff_limit

class EndpointState():
  def __init__(self, configuration: EndpointConfiguration, last_checked: float = 0.0, previous_status_code: int = None, previous_body: str = None):
    self.configuration = configuration
    self.last_checked = last_checked
    self.previous_status_code = previous_status_code
    self.previous_body = previous_body

def log(msg: str, is_error: bool = False):
  if is_error:
    print(msg, file=sys.stderr)
  else:
    print(msg)

def check_endpoint(state: EndpointState, attempt: int = 0):
  try:
    res = requests.get(state.configuration.url)
    if state.previous_status_code is None:
      state.previous_status_code = res.status_code
      state.previous_body = res.text
      return
    if res.status_code != state.previous_status_code:
      error_message = "{}: Status code changed from {} to {}".format(state.configuration.name, state.previous_status_code, res.status_code)
      log(error_message, True)
      state.previous_status_code = res.status_code
      state.previous_body = res.text
      return
    elif res.text != state.previous_body:
      percent_changed = distance(state.previous_body, res.text) / len(state.previous_body)
      if percent_changed > (state.configuration.percent_diff_limit + 0.0000000001): # Handle computer number issues
        error_message = "{}: Body changed by {}%".format(state.configuration.name, int(percent_changed * 100))
        log(error_message, True)
        state.previous_body = res.text
      return
  except requests.ReadTimeout as e:
    if attempt < 3:
      log("{}: Retrying due to readtimeout".format(state.configuration.name))
      time.sleep(1)
      return check_endpoint(state, attempt + 1)
    if state.previous_status_code != -1:
      error_message = "{}: Endpoint no longer available: {}".format(state.configuration.name, type(e).__name__)
      log(error_message, True)
      state.previous_status_code = -1
      state.previous_body = ""
    return
  except Exception as e:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    emsg = '\n'.join(lines)
    log(emsg)

    if state.previous_status_code != -1:
      error_message = "{}: Endpoint no longer available: {}".format(state.configuration.name, type(e).__name__)
      log(error_message, True)
      state.previous_status_code = -1
      state.previous_body = ""
    return



states: List[EndpointState] = []

with open(args.config_file, 'r') as file:
  config = yaml.safe_load(file)
  for endpoint in config['endpoints']:
    configuration = EndpointConfiguration(
      endpoint['name'] if 'name' in endpoint else endpoint['url'],
      endpoint['url'],
      int(endpoint['interval']),
      float(endpoint['percent_diff_limit'])/100.0 if 'percent_diff_limit' in endpoint else 0.00
    )
    state = EndpointState(configuration)
    states.append(state)

while True:
  t = time.time()
  for state in states:
    if (state.last_checked + state.configuration.interval) < t:
      log("{}: Checking endpoint".format(state.configuration.name))
      check_endpoint(state)
      log("{}: Done".format(state.configuration.name))
      state.last_checked = t
  time.sleep(1)
