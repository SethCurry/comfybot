import typing

from dataclasses import dataclass

WorkflowCustomizer = typing.Callable[[typing.Dict[str, typing.Any]], typing.Dict[str, typing.Any]]

@dataclass
class QueuePromptResponse:
  prompt_id: str
  number: int
  node_errors: typing.Dict[str, typing.Any]

class ImageOutput:
  def __init__(self, filename: str, image_type: str, subfolder: str = ""):
    self.filename = filename
    self.subfolder = subfolder
    self.image_type = image_type
  
  def validate(self):
    if self.filename == "":
      raise ValueError("filename cannot be empty")
    if self.image_type == "":
      raise ValueError("image_type cannot be empty")
  
  @staticmethod
  def from_json(data: typing.Dict[str, typing.Any]) -> "ImageOutput":
    img = ImageOutput(
      filename=data.get("filename", ""),
      subfolder=data.get("subfolder", ""),
      image_type=data.get("type", "")
    )
    img.validate()
    return img

class PromptOutput:
  def __init__(self, images: typing.Optional[typing.List[ImageOutput]] = None):
    self.images = images
  
  def validate(self):
    if self.images is None:
      raise ValueError("images cannot be None")
  
  @staticmethod
  def from_json(data: typing.Dict[str, typing.Any]) -> "PromptOutput":
    images = data.get("images", [])

    parsed_images = []

    for img in images:
      parsed = ImageOutput.from_json(img)
      parsed.validate()
      parsed_images.append(parsed)

    return PromptOutput(images=parsed_images)

class PromptStatus:
  def __init__(self, status_str: str, completed: bool):
    self.status_str = status_str
    self.completed = completed
  
  def validate(self):
    if self.status_str == "":
      raise ValueError("status_str cannot be empty")
  
  @staticmethod
  def from_json(data: typing.Dict[str, typing.Any]) -> "PromptStatus":
    return PromptStatus(
      status_str=data.get("status_str", ""),
      completed=data.get("completed", False)
    )

class PromptHistory:
  def __init__(self, status: PromptStatus, outputs: typing.Optional[typing.Dict[str, PromptOutput]] = None):
    self.status = status
    self.outputs = outputs
  
  def validate(self):
    self.status.validate()
    
    if self.outputs is not None:
      [o.validate() for o in self.outputs.values()]
  
  @staticmethod
  def from_json(data: typing.Dict[str, typing.Any]) -> "PromptHistory":
    status = PromptStatus.from_json(data.get("status", {}))
    outputs = data.get("outputs", {})

    parsed_outputs = {}

    for key, output in outputs.items():
      parsed_outputs[key] = PromptOutput.from_json(output)

    pro = PromptHistory(status=status, outputs=parsed_outputs)

    # inefficient, will re-validate all the components, but that should be fine.
    # this isn't high-performance code
    pro.validate()

    return pro

PromptHistoryResponse = typing.Dict[str, PromptHistory]
