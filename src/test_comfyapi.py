import pytest

import comfyapi

def test_is_prompt_done():
  test_cases = [
    [{}, False],
    [{'status': {}}, False],
    [{'status': {'completed': False}}, False],
    [{'status': {'completed': True}}, True],
  ]

  for tc in test_cases:
    assert comfyapi.is_prompt_done(tc[0]) == tc[1]