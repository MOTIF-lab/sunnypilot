import os

from openpilot.common.api import Api as CommaApi
from openpilot.common.api.base import BaseApi

API_HOST = os.getenv('MOTIF_HOST', 'https://op-api.motiflab.net')


class MotifUploadAPI(BaseApi):
  def __init__(self, dongle_id):
    super().__init__(dongle_id, API_HOST)
    self.user_agent = "openpilot-"


class Api(CommaApi):
  def __init__(self, dongle_id):
    super().__init__(dongle_id)
    self.service = MotifUploadAPI(dongle_id)
