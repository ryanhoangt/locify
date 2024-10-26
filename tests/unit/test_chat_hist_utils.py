from locify.utils.chat_history import get_file_mentions, get_identifier_mentions


def test_get_file_mentions_basic_mention():
    rel_paths = ['src/utils.py', 'src/data_loader.py']
    text = 'Please check the src/utils.py for details.'
    assert get_file_mentions(rel_paths, text) == {'src/utils.py'}


def test_get_file_mentions_by_filename_only():
    rel_paths = ['src/utils.py']
    text = 'Refer to utils.py for utility functions.'
    assert get_file_mentions(rel_paths, text) == {'src/utils.py'}


def test_get_file_mentions_multiple_mentions_by_basename():
    rel_paths = ['src/utils.py', 'lib/utils.py']
    text = 'Check utils.py for the common functionality.'
    assert get_file_mentions(rel_paths, text) == set()


def test_get_file_mentions_punctuation_and_quotes():
    rel_paths = ['src/utils.py', 'docs/readme.txt']
    text = 'Refer to "utils.py" and `readme.txt` for setup instructions!'
    assert set(get_file_mentions(rel_paths, text)) == {
        'src/utils.py',
        'docs/readme.txt',
    }


def test_get_file_mentions_punctuation_and_no_quotes():
    rel_paths = ['src/utils.py', 'docs/readme.txt']
    text = 'Refer to utils.py and readme.txt for setup instructions!'
    assert set(get_file_mentions(rel_paths, text)) == {
        'src/utils.py',
        'docs/readme.txt',
    }


def test_get_identifier_mentions_basic_words():
    text = 'word1 word2 word3'
    assert set(get_identifier_mentions(text)) == {'word1', 'word2', 'word3'}


def test_get_identifier_mentions_non_alphanumeric_split():
    text = 'func1(), func2! &func3*'
    assert set(get_identifier_mentions(text)) == {'func1', 'func2', 'func3'}


def test_get_identifier_mentions_remove_empty_strings():
    text = ' , ; ; ; '
    assert get_identifier_mentions(text) == set()


def test_get_identifier_mentions_mixed_content():
    text = 'a1_b2, and func3-hello'
    assert set(get_identifier_mentions(text)) == {'a1_b2', 'and', 'func3', 'hello'}


def test_get_identifier_mentions_no_identifiers():
    text = '!!! @@ ##'
    assert get_identifier_mentions(text) == set()
