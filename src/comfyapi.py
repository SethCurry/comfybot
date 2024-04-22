import asyncio
import json
import typing

from dataclasses import dataclass
from loguru import logger

import aiohttp

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

def is_prompt_done(resp: typing.Dict[str, typing.Any]) -> bool:
  if 'status' not in resp:
    return False

  if 'completed' not in resp['status']:
    return False

  return resp['status']['completed']

class Client:
  def __init__(self, baseurl: str):
    self.baseurl = baseurl
  
  async def queue_prompt(self, workflow: typing.Dict[str, typing.Any]) -> QueuePromptResponse:
    data = json.dumps({'prompt': workflow}).encode('utf-8')

    async with aiohttp.ClientSession() as session:
      async with session.post(f'{self.baseurl}/prompt', data=data, headers={'Content-Type': 'application/json'}) as req:
        resp = await req.json()
        return QueuePromptResponse(prompt_id=resp['prompt_id'], number=resp['number'], node_errors=resp['node_errors'])
  
  async def free(self, unload_models=False, free_memory=False):
    async with aiohttp.ClientSession() as session:
      async with session.post(f'{self.baseurl}/free', params={
        'unload_models': unload_models,
        'free_memory': free_memory,
      }) as req:
        if req.status != 200:
          raise Exception(f'Failed to free: {await req.text()}')
  
  async def get_image(self, filename: str, subfolder: str, img_type: str):
    async with aiohttp.ClientSession() as session:
      async with session.get(f'{self.baseurl}/view', params={
        'filename': filename,
        'subfolder': subfolder,
        'type': img_type,
      }) as req:
        if req.status != 200:
          text = await req.text()
          raise Exception(f'Failed to get image: {text}')
        return await req.read()
  
  async def wait_for_image(self, prompt_id: str):
    iters = 0
    pollIntervalSeconds = 5

    async with aiohttp.ClientSession() as session:
      while iters < 60:
        logger.info('Polling for image')

        await asyncio.sleep(pollIntervalSeconds)

        images: typing.List[ImageOutput] = []

        iters += 1

        async with session.get(f'{self.baseurl}/history/{prompt_id}') as req:
          resp = await req.json()

          if prompt_id not in resp:
            logger.debug('Prompt not in response')
            continue
          resp = resp[prompt_id]

          logger.debug(resp)

          if not is_prompt_done(resp):
            logger.debug('prompt not done')
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
