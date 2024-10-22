# import warnings
from collections import namedtuple
from enum import Enum
from pathlib import Path

from grep_ast import filename_to_lang
from tree_sitter_languages import get_language, get_parser

from locify.utils.file import read_text

# warnings.simplefilter('ignore', category=FutureWarning)

ParsedTag = namedtuple(
    'ParsedTag', ('rel_path', 'abs_path', 'start_line', 'node_name', 'tag_kind')
)


class TagKind(Enum):
    DEF = 'def'
    REF = 'ref'


class TreeSitterParser:
    def __init__(self) -> None:
        pass

    def get_tags_from_file(self, abs_path: str, rel_path: str) -> list[ParsedTag]:
        lang = filename_to_lang(abs_path)
        if not lang:
            return []

        ts_language = get_language(lang)
        ts_parser = get_parser(lang)

        tags_file_path = (
            Path(__file__).resolve().parent / 'queries' / f'tree-sitter-{lang}-tags.scm'
        )
        if not tags_file_path.exists():
            return []
        tags_query = tags_file_path.read_text()

        if not Path(abs_path).exists():
            return []
        code = read_text(abs_path)
        if not code:
            return []

        parsed_tree = ts_parser.parse(bytes(code, 'utf-8'))

        # Run the tags queries
        query = ts_language.query(tags_query)
        captures = query.captures(parsed_tree.root_node)

        parsed_tags = []
        for node, tag_str in captures:
            if tag_str.startswith('name.definition.'):
                tag_kind = TagKind.DEF
            elif tag_str.startswith('name.reference.'):
                tag_kind = TagKind.REF
            else:
                # Skip other tags
                continue

            result_tag = ParsedTag(
                rel_path=rel_path,
                abs_path=abs_path,
                start_line=node.start_point[0],
                node_name=node.text.decode(
                    'utf-8'
                ),  # node_name is defined in the query file
                tag_kind=tag_kind,
            )
            parsed_tags.append(result_tag)

        return parsed_tags
