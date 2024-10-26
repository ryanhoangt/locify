import os
import re


def get_file_mentions(rel_paths: list[str], full_messages_text: str) -> set[str]:
    words = set(word for word in full_messages_text.split())

    # Drop sentence punctuation from the end
    words = set(word.rstrip(',.!;:?') for word in words)

    # Strip away all kinds of quotes
    quotes = ''.join(['"', "'", '`'])
    words = set(word.strip(quotes) for word in words)

    mentioned_rel_paths = set()
    fname_to_rel_fnames: dict = {}
    for rel_path in rel_paths:
        if rel_path in words:
            mentioned_rel_paths.add(str(rel_path))

        fname = os.path.basename(rel_path)

        # Don't add basenames that could be plain words like "run" or "make"
        if '/' in fname or '.' in fname or '_' in fname or '-' in fname:
            if fname not in fname_to_rel_fnames:
                fname_to_rel_fnames[fname] = []
            fname_to_rel_fnames[fname].append(rel_path)

    for fname, rel_fnames in fname_to_rel_fnames.items():
        if len(rel_fnames) == 1 and fname in words:
            mentioned_rel_paths.add(rel_fnames[0])

    return mentioned_rel_paths


def get_identifier_mentions(text: str) -> set[str]:
    # Split the string on any character that is not alphanumeric
    # \W+ matches one or more non-word characters (equivalent to [^a-zA-Z0-9_]+)
    words = set(re.split(r'\W+', text))
    # Remove empty strings
    words = set(word for word in words if word)
    return words
