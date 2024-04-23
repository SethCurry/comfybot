import asyncio
import json
import typing

import aiohttp

from loguru import logger

from . import models


def is_prompt_done(resp: typing.Dict[str, typing.Any]) -> bool:
  if 'status' not in resp:
    return False

  if 'completed' not in resp['status']:
    return False

  return resp['status']['completed']


class Client:
  def __init__(self, baseurl: str):
    self.baseurl = baseurl
  
  async def queue_prompt(self, workflow: typing.Dict[str, typing.Any]) -> models.QueuePromptResponse:
    data = json.dumps({'prompt': workflow}).encode('utf-8')

    async with aiohttp.ClientSession() as session:
      async with session.post(f'{self.baseurl}/prompt', data=data, headers={'Content-Type': 'application/json'}) as req:
        resp = await req.json()
        return models.QueuePromptResponse(prompt_id=resp['prompt_id'], number=resp['number'], node_errors=resp['node_errors'])
  
  async def free(self, unload_models=False, free_memory=False) -> None:
    async with aiohttp.ClientSession() as session:
      async with session.post(f'{self.baseurl}/free', params={
        'unload_models': unload_models,
        'free_memory': free_memory,
      }) as req:
        if req.status != 200:
          raise Exception(f'Failed to free: {await req.text()}')
  
  async def get_image(self, filename: str, subfolder: str, img_type: str) -> bytes:
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
  
  async def prompt_history(self, prompt_id: typing.Optional[str] = None):
    query_url = f'{self.baseurl}/history'
    if prompt_id is not None:
      query_url = f'{query_url}/{prompt_id}'
    
    async with aiohttp.ClientSession() as session:
      async with session.get(query_url) as req:
        data = await req.json()

        prompts: models.PromptHistoryResponse = {}
        
        for prompt_id, prompt_data in data.items():
          prompts[prompt_id] = models.PromptHistory.from_json(prompt_data)
        
        return prompts
  
  async def wait_for_image(self, prompt_id: str, max_attempts=60, poll_interval_seconds=5):
    iters = 0

    while iters < max_attempts:
      logger.info('Polling for image')

      await asyncio.sleep(poll_interval_seconds)

      iters += 1

      prompts = await self.prompt_history(prompt_id=prompt_id)

      if prompt_id not in prompts:
        logger.debug('Prompt not in response')
        continue

      prompt = prompts[prompt_id]

      if not prompt.status.completed:
        logger.debug('prompt not done')
        continue

      if prompt.outputs is None:
        logger.debug('No outputs in response')
        continue

      images: typing.List[models.ImageOutput] = []

      for output in prompt.outputs.values():
        for img in output.images:
          images.append(img)
    
      if len(images) > 0:
        return images

    raise Exception('Timed out waiting for image')  
