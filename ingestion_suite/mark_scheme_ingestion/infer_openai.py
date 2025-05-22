import os

from azure.ai.inference.models import (
    SystemMessage,
    UserMessage,
    JsonSchemaFormat
    )

from typing import List

from pydantic import BaseModel
from helpers import get_llm, load_image_as_data_url

def invoke_openai(
    prompt: str,
    model_name: str,
    output_format: BaseModel = None,
    payload: List[UserMessage] = None
) -> str:
    client = get_llm(model_name)
    request_kwargs = {
        "messages": [SystemMessage(content=prompt), *payload],
        "model": model_name,
    }

    if output_format is not None:
        request_kwargs["response_format"] = JsonSchemaFormat(
            name="output_format",
            schema=output_format.model_json_schema()
        )

    response = client.complete(**request_kwargs)

    return response.choices[0].message.content

if __name__ == "__main__":
    image_path = "June 2020 MS_images\\page_6.png"
    data_url = load_image_as_data_url(image_path)

    response = invoke_openai(
        image=data_url,
        prompt="Describe whats in this image",
        model_name="gpt-4.1"
    )
    print(response)