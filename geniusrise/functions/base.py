from pydantic import BaseModel, create_model
from typing import Callable
import inspect
import json
from markdown_it import MarkdownIt


class FunctionWrapper:
    def __init__(self, func: Callable, input_schema: BaseModel, output_schema: BaseModel):
        self.func = func
        self.input_schema = input_schema
        self.output_schema = output_schema

    @staticmethod
    def create(func: Callable):
        sig = inspect.signature(func)

        # Check that all parameters and the return value have type annotations
        for param in sig.parameters.values():
            if param.annotation is param.empty:
                raise TypeError(f"Missing type annotation for parameter '{param.name}'")
        if sig.return_annotation is sig.empty:
            raise TypeError("Missing type annotation for return value")

        # Create the input schema
        input_schema_dict = {k: (v.annotation, ...) for k, v in sig.parameters.items()}
        input_schema = create_model("DynamicInputModel", **input_schema_dict)

        # Create the output schema
        output_schema = create_model("DynamicOutputModel", return_value=(sig.return_annotation, ...))

        return FunctionWrapper(func, input_schema, output_schema)

    def __call__(self, *args, **kwargs):
        # Convert args to kwargs
        sig = inspect.signature(self.func)
        kwargs.update(sig.bind_partial(*args).arguments)

        # Validate kwargs
        validated_data = self.input_schema(**kwargs)

        # Call the function with validated arguments
        result = self.func(**validated_data.dict())

        # Validate the result
        validated_result = self.output_schema(return_value=result)

        return validated_result.return_value

    def validate_args(self, *args, **kwargs):
        # Convert args to kwargs
        sig = inspect.signature(self.func)
        kwargs.update(sig.bind_partial(*args).arguments)

        # Validate kwargs
        return self.schema(**kwargs)

    def compose(self, other):
        # Check that the output type of 'other' matches the input type of 'self'
        other_output_type = other.output_schema.return_value.annotation
        self_input_type = next(iter(self.input_schema.__annotations__.values()))
        if other_output_type != self_input_type:
            raise TypeError("The functions are not composable")

        # Define the composed function
        def composed(*args, **kwargs):
            return self(other(*args, **kwargs))

        # Create a new FunctionWrapper for the composed function
        return FunctionWrapper.create(composed)

    def llm_compose(self, other, prompt, llm_api):
        self_input_type = next(iter(self.input_schema.__annotations__.values()))

        # Define the composed function
        def composed(*args, **kwargs):
            # Call the first function
            other_result = other(*args, **kwargs)

            # Generate the LLM prompt
            llm_prompt = f"{prompt}\n\nOutput: {other_result}\n\nInput format: {self_input_type}"

            # Call the LLM API
            llm_output = llm_api.generate(llm_prompt)

            # Extract the first code block
            code_block = self._extract_first_code_block(llm_output)

            # Parse the code block as JSON
            transformed_result = json.loads(code_block)

            # Call the second function
            return self(**transformed_result)

        # Create a new FunctionWrapper for the composed function
        return FunctionWrapper.create(composed)

    @staticmethod
    def _extract_first_code_block(text):
        md = MarkdownIt()
        tokens = md.parse(text)
        for token in tokens:
            if token.type == "fence" and token.info == "python":
                return token.content
        raise ValueError("No code block found in LLM output")


def action(func):
    return FunctionWrapper.create(func)
