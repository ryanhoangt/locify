from collections import defaultdict
from pathlib import Path

from grep_ast import TreeContext

from locify.tree_sitter.parser import ParsedTag, TagKind, TreeSitterParser
from locify.utils.file import GitRepoUtils, read_text
from locify.utils.llm import get_token_count_from_text
from locify.utils.path import PathUtils


class FullMapStrategy:
    def __init__(self, model_name='gpt-4o', root='./') -> None:
        if not Path(root).is_absolute():
            root = str(Path(root).resolve())

        self.root = root
        self.model_name = model_name

        self.git_utils = GitRepoUtils(root)
        self.path_utils = PathUtils(root)
        self.ts_parser = TreeSitterParser()

    def get_map(self, depth: int | None = None, rel_dir_path: str | None = None) -> str:
        ranked_tags = self.get_ranked_tags(rel_dir_path=rel_dir_path, depth=depth)
        tree_repr = self.tag_list_to_tree(ranked_tags)
        return tree_repr

    def get_map_with_token_count(
        self, depth: int | None = None, rel_dir_path: str | None = None
    ) -> str:
        tree_repr = self.get_map(depth=depth, rel_dir_path=rel_dir_path)
        token_count = get_token_count_from_text(self.model_name, tree_repr)
        return f'{tree_repr}\n\nToken count: {token_count}'

    def get_ranked_tags(
        self, depth: int | None = None, rel_dir_path: str | None = None
    ) -> list[ParsedTag]:
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

        for abs_file in all_abs_files:
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

        context.add_lines_of_interest(lois)
        context.add_context()
        res = context.format()
        return res
