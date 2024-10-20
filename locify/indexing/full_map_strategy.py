from collections import defaultdict

from locify.tree_sitter.parser import ParsedTag, TagKind, TreeSitterParser
from locify.utils.file import GitRepoUtils
from locify.utils.path import PathUtils


class FullMapStrategy:
    
    def __init__(self, model_name='gpt-4o', root='./') -> None:
        self.root = root
        self.model_name = model_name

        self.git_utils = GitRepoUtils(root)
        self.path_utils = PathUtils(root)
        self.ts_parser = TreeSitterParser()
        
    def get_map(self) -> str:
        ranked_tags = self.get_ranked_tags()
        for tag in ranked_tags:
            print(tag)

    def get_ranked_tags(self) -> list[ParsedTag]:
        all_abs_files = self.git_utils.get_all_absolute_tracked_files()

        ident2defrels = defaultdict(set) # symbol identifier -> set of its definitions' relative file paths
        ident2refrels = defaultdict(list) # symbol identifier -> list of its references' relative file paths
        identwrel2tags = defaultdict(set) # (relative file, symbol identifier) -> set of its tags
        
        for abs_file in all_abs_files:
            rel_file = self.path_utils.get_relative_path_str(abs_file)
            parsed_tags = self.ts_parser.get_tags_from_file(abs_file, rel_file)
            
            for parsed_tag in parsed_tags:
                if parsed_tag.tag_kind == TagKind.DEF:
                    ident2defrels[parsed_tag.node_name].add(rel_file)
                    identwrel2tags[(rel_file, parsed_tag.node_name)].add(parsed_tag)
                if parsed_tag.tag_kind == TagKind.REF:
                    ident2refrels[parsed_tag.node_name].append(rel_file)
        
        # all_idents = set(ident2defrels.keys()) | set(ident2refrels.keys())
        # print(all_idents)
        
        # Sort tags by relative file path and tag's line number
        all_tags = []
        for tags in identwrel2tags.values():
            all_tags.extend(tags)
        all_tags.sort(key=lambda tag: (tag.rel_path, tag.start_line))
        return all_tags
        
if __name__ == '__main__':
    strategy = FullMapStrategy()
    print(strategy.get_map())