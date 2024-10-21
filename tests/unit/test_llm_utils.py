from locify.utils.llm import get_token_count_from_text


def test_get_token_count_from_text():
    model_name = 'gpt2'
    text = 'Hello, world!'
    assert get_token_count_from_text(model_name, text) == 4
