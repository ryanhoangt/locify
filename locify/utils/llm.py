import litellm


def get_token_count_from_text(model_name: str, text: str) -> int:
    return litellm.token_counter(model=model_name, text=text)
