def generate_prompts_from_x(x: str):
    return f"""
generate 10 prompts to generate this {x} (that i intend to use to  fine tune a model to be able to generate this {x} when prompted by those prompts):

"""
