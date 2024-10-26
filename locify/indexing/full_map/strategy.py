from collections import defaultdict
from pathlib import Path

from grep_ast import TreeContext
from tqdm import tqdm

from locify.indexing.prompts import Prompts
from locify.tree_sitter.parser import ParsedTag, TagKind, TreeSitterParser
from locify.utils.chat_history import get_file_mentions, get_identifier_mentions
from locify.utils.file import GitRepoUtils, get_modified_time, read_text
from locify.utils.llm import get_token_count_from_text
from locify.utils.path import PathUtils


class FullMapStrategy:
    def __init__(
        self,
        model_name='gpt-4o',
        root='./',
        max_map_token=1024 * 3,
        content_prefix=Prompts.repo_content_prefix,
    ) -> None:
        if not Path(root).is_absolute():
            root = str(Path(root).resolve())

        self.root = root
        self.model_name = model_name
        self.max_map_token = max_map_token
        self.content_prefix = content_prefix

        self.git_utils = GitRepoUtils(root)
        self.path_utils = PathUtils(root)
        self.ts_parser = TreeSitterParser(self.root)

        # Caching
        self.file_context_cache: dict = {}  # (rel_file) -> {'context': TreeContext_obj, 'mtime': mtime})
        self.rendered_tree_cache: dict = {}  # (rel_file, lois, mtime) -> rendered_tree

    def tags_to_tree(self, parsed_tags: list[ParsedTag]) -> str:
        num_tags = len(parsed_tags)
        lower_bound, upper_bound = 0, num_tags
        best_tree_token_count = 0

        # Assume each tag has 16 tokens on average, this trick is to deal with repos with lots of tags and using the exact middle as the starting point is too slow
        mid = min(self.max_map_token // 16, num_tags) // 2
        while lower_bound < upper_bound:
            tree_repr = self.tag_list_to_tree(parsed_tags[:mid])
            token_count = get_token_count_from_text(self.model_name, tree_repr)

            if (
                token_count <= self.max_map_token
                and token_count > best_tree_token_count
            ):
                best_tree_token_count = token_count

            if token_count > self.max_map_token:
                upper_bound = mid
            else:
                lower_bound = mid + 1

            mid = (lower_bound + upper_bound) // 2

        result_tags = parsed_tags[:mid]
        # Sort by relative file path and tag's line number
        result_tags.sort(key=lambda tag: (tag.rel_path, tag.start_line))
        return self.tag_list_to_tree(result_tags)

    def get_map(
        self,
        depth: int | None = None,
        rel_dir_path: str | None = None,
        message_history: str = '',
    ) -> str:
        # t0 = time.time()
        tracked_rel_files = self.git_utils.get_all_relative_tracked_files(depth=depth)
        mentioned_rel_files = get_file_mentions(tracked_rel_files, message_history)
        mentioned_identifiers = get_identifier_mentions(message_history)

        ranked_tags = self.get_ranked_tags(
            rel_dir_path=rel_dir_path,
            depth=depth,
            mentioned_rel_files=mentioned_rel_files,
            mentioned_idents=mentioned_identifiers,
        )
        tree_repr = self.tags_to_tree(ranked_tags)
        # print(f'Getting map took {time.time() - t0:.2f}s')
        return self.content_prefix + tree_repr

    def get_map_with_token_count(
        self,
        depth: int | None = None,
        rel_dir_path: str | None = None,
        message_history: str = '',
    ) -> str:
        tree_repr = self.get_map(
            depth=depth, rel_dir_path=rel_dir_path, message_history=message_history
        )
        token_count = get_token_count_from_text(self.model_name, tree_repr)
        return f'{tree_repr}\n\nToken count: {token_count}'

    def get_ranked_tags(
        self,
        depth: int | None = None,
        rel_dir_path: str | None = None,
        mentioned_rel_files: set | None = None,
        mentioned_idents: set | None = None,
    ) -> list[ParsedTag]:
        # TODO: Implement higher ranking for mentioned files and identifiers

        if rel_dir_path:
            all_abs_files = self.git_utils.get_absolute_tracked_files_in_directory(
                rel_dir_path=rel_dir_path,
                depth=depth,
            )
        else:
            all_abs_files = self.git_utils.get_all_absolute_tracked_files(depth=depth)

        identwrel2tags = defaultdict(
            set
        )  # (relative file, symbol identifier) -> set of its tags

        for abs_file in tqdm(all_abs_files, desc='Parsing tags', unit='file'):
            rel_file = self.path_utils.get_relative_path_str(abs_file)
            parsed_tags = self.ts_parser.get_tags_from_file(abs_file, rel_file)

            for parsed_tag in parsed_tags:
                if parsed_tag.tag_kind == TagKind.DEF:
                    identwrel2tags[(rel_file, parsed_tag.node_name)].add(parsed_tag)

        # Sort tags by relative file path and tag's line number
        all_tags: list[ParsedTag] = []
        for tags in identwrel2tags.values():
            all_tags.extend(tags)
        all_tags.sort(key=lambda tag: (tag.rel_path, tag.start_line))
        return all_tags

    def tag_list_to_tree(self, tags: list[ParsedTag]) -> str:
        if not tags:
            return ''

        cur_rel_file, cur_abs_file = '', ''
        lois: list[int] = []
        output = ''

        dummy_tag = ParsedTag(
            abs_path='', rel_path='', node_name='', tag_kind=TagKind.DEF, start_line=0
        )
        for tag in tags + [dummy_tag]:  # Add dummy tag to trigger last file output
            if tag.rel_path != cur_rel_file:
                if lois:
                    output += cur_rel_file + ':\n'
                    output += self.render_tree(cur_abs_file, cur_rel_file, lois)
                    lois = []
                elif cur_rel_file:  # No line of interest
                    output += '\n' + cur_rel_file + ':\n'

                cur_abs_file = tag.abs_path
                cur_rel_file = tag.rel_path

            lois.append(tag.start_line)

        # Truncate long lines in case we get minified js or something else crazy
        output = '\n'.join(line[:150] for line in output.splitlines())
        return output

    def render_tree(self, abs_file: str, rel_file: str, lois: list) -> str:
        mtime = get_modified_time(abs_file)
        tree_cache_key = (rel_file, tuple(sorted(lois)), mtime)
        if tree_cache_key in self.rendered_tree_cache:
            return self.rendered_tree_cache[tree_cache_key]

        if (
            rel_file not in self.file_context_cache
            or self.file_context_cache[rel_file]['mtime'] < mtime
        ):
            code = read_text(abs_file) or ''
            if not code.endswith('\n'):
                code += '\n'

            context = TreeContext(
                filename=rel_file,
                code=code,
                color=False,
                line_number=True,
                child_context=False,
                last_line=False,
                margin=0,
                mark_lois=False,
                loi_pad=0,
                # header_max=30,
                show_top_of_file_parent_scope=False,
            )
            self.file_context_cache[rel_file] = {'context': context, 'mtime': mtime}
        else:
            context = self.file_context_cache[rel_file]['context']

        context.lines_of_interest = set()
        context.add_lines_of_interest(lois)
        context.add_context()
        res = context.format()
        self.rendered_tree_cache[tree_cache_key] = res
        return res
