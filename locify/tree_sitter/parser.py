# import warnings
from collections import namedtuple
from enum import Enum
from pathlib import Path

from diskcache import Cache
from grep_ast import filename_to_lang
from tree_sitter_languages import get_language, get_parser

from locify.utils.file import get_modified_time, read_text

# warnings.simplefilter('ignore', category=FutureWarning)

ParsedTag = namedtuple(
    'ParsedTag', ('rel_path', 'abs_path', 'start_line', 'node_name', 'tag_kind')
)


class TagKind(Enum):
    DEF = 'def'
    REF = 'ref'


class TreeSitterParser:
    TAGS_CACHE_VERSION = 3
    TAGS_CACHE_DIR = f'.cache.tags.v{TAGS_CACHE_VERSION}'

    def __init__(self, cache_root_dir: str) -> None:
        self.load_tags_cache(cache_root_dir)

    def load_tags_cache(self, abs_root_dir: str) -> None:
        cache_path = Path(abs_root_dir) / self.TAGS_CACHE_DIR
        try:
            self.tags_cache = Cache(cache_path)
        except Exception:
            print(
                f'Could not load tags cache from {cache_path}, try deleting cache directory.'
            )
            self.tags_cache = dict()

    def get_tags_from_file(self, abs_path: str, rel_path: str) -> list[ParsedTag]:
        mtime = get_modified_time(abs_path)
        cache_key = abs_path
        cache_val = self.tags_cache.get(cache_key)
        if cache_val and cache_val.get('mtime') == mtime:
            return cache_val.get('data')

        data = self.get_tags_raw(abs_path, rel_path)
        # Update cache
        self.tags_cache[cache_key] = {'mtime': mtime, 'data': data}
        return data

    def get_tags_raw(self, abs_path: str, rel_path: str) -> list[ParsedTag]:
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
