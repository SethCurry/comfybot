import asyncio
import json
import time
import typing

from enum import StrEnum
from dataclasses import dataclass
from loguru import logger

import requests

WorkflowCustomizer = typing.Callable[[typing.Dict[str, typing.Any]], typing.Dict[str, typing.Any]]

@dataclass
class QueuePromptResponse:
  prompt_id: str
  number: int
  node_errors: typing.Dict[str, typing.Any]

@dataclass
class ImageOutput:
  filename: str
  subfolder: str
  image_type: str

class Client:
  def __init__(self, baseurl: str):
    self.baseurl = baseurl
  
  def queue_prompt(self, workflow: typing.Dict[str, typing.Any]) -> QueuePromptResponse:
    data = json.dumps({'prompt': workflow}).encode('utf-8')

    resp = requests.post(f'{self.baseurl}/prompt', data=data, headers={'Content-Type': 'application/json'}).json()

    return QueuePromptResponse(prompt_id=resp['prompt_id'], number=resp['number'], node_errors=resp['node_errors'])
  
  def free(self, unload_models=False, free_memory=False):
    requests.post(f'{self.baseurl}/free', params={
      'unload_models': unload_models,
      'free_memory': free_memory,
    })
  
  def get_image(self, filename: str, subfolder: str, img_type: str):
    resp =  requests.get(f'{self.baseurl}/view', params={
      'filename': filename,
      'subfolder': subfolder,
      'type': img_type,
    })

    if resp.status_code != 200:
      raise Exception(f'Failed to get image: {resp.text}')

    return resp.content
  
  async def wait_for_image(self, prompt_id: str):
    iters = 0
    pollIntervalSeconds = 5

    while iters < 60:
      logger.info('Polling for image')

      await asyncio.sleep(pollIntervalSeconds)

      images: typing.List[ImageOutput] = []

      iters += 1

      resp = requests.get(f'{self.baseurl}/history/{prompt_id}').json()

      if prompt_id not in resp:
        logger.debug('Prompt not in response')
        continue
      resp = resp[prompt_id]

      logger.debug(resp)

      if 'status' not in resp:
        logger.debug('No status in response')
        continue

      if resp['status']['completed'] != True:
        logger.debug('Prompt not completed')
        continue

      if 'outputs' not in resp:
        logger.debug('No outputs in response')
        continue

      outputs = resp['outputs']

      for output in outputs.values():
        if 'images' not in output:
          logger.debug('No images in output')
          continue

        for img in output['images']:
          images.append(ImageOutput(filename=img['filename'], subfolder=img['subfolder'], image_type=img['type']))
      
      if len(images) > 0:
        return images

    raise Exception('Timed out waiting for image')  
