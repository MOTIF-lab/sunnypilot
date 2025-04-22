#!/usr/bin/env python3
import random
import threading
import time

import cereal.messaging as messaging
from openpilot.motifpilot.motif_api import Api
from cereal import log
from openpilot.common.params import Params
from openpilot.common.realtime import set_core_affinity
from openpilot.common.swaglog import cloudlog
from openpilot.system.hardware.hw import Paths
from openpilot.system.loggerd.uploader import Uploader as OPUploader
from openpilot.system.loggerd.uploader import (allow_sleep, clear_locks,
                                               force_wifi)

NetworkType = log.DeviceState.NetworkType

class DatasetUploader(OPUploader):
  def __init__(self, dongle_id: str, root: str) -> None:
    super().__init__(dongle_id, root)
    self.api = Api(dongle_id)
    self.immediate_priority.update({
      'rlog': 2,
      'rlog.zst': 2,
      'fcamera.hevc': 4,
      'ecamera.hevc': 4,
      'dcamera.hevc': 6,
    })
    self.upload_attr_name, self.upload_attr_value = 'user.motif.upload', b'1'


def main(exit_event: threading.Event = None) -> None:
  if exit_event is None:
    exit_event = threading.Event()

  try:
    set_core_affinity([0, 1, 2, 3])
  except Exception:
    cloudlog.exception("failed to set core affinity")

  clear_locks(Paths.log_root())

  params = Params()
  dongle_id = params.get("DongleId", encoding='utf8')

  if dongle_id is None:
    cloudlog.info("uploader missing dongle_id")
    raise Exception("uploader can't start without dongle id")

  sm = messaging.SubMaster(['deviceState'])
  uploader = DatasetUploader(dongle_id, Paths.log_root())

  backoff = 0.1
  while not exit_event.is_set():
    sm.update(0)
    offroad = params.get_bool("IsOffroad")
    network_type = sm['deviceState'].networkType if not force_wifi else NetworkType.wifi
    if network_type == NetworkType.none:
      if allow_sleep:
        time.sleep(60 if offroad else 5)
      continue

    success = uploader.step(sm['deviceState'].networkType.raw, sm['deviceState'].networkMetered)
    if success is None:
      backoff = 60 if offroad else 5
    elif success:
      backoff = 0.1
    else:
      cloudlog.info("upload backoff %r", backoff)
      backoff = min(backoff * 2, 120)
    if allow_sleep:
      time.sleep(backoff + random.uniform(0, backoff))


if __name__ == "__main__":
  main()
