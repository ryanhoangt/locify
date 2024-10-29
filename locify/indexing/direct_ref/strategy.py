from collections import defaultdict

from tqdm import tqdm

from locify.indexing.direct_ref.extractor import extract_identifiers_from_text
from locify.indexing.full_map.strategy import FullMapStrategy
from locify.indexing.prompts import Prompts
from locify.tree_sitter.parser import TagKind
from locify.utils.llm import get_token_count_from_text


class DirectRefStrategy(FullMapStrategy):
    def __init__(
        self,
        model_name='gpt-4o',
        root='./',
        max_map_token=1024 * 3,
        show_progress=False,
    ) -> None:
        super().__init__(model_name, root, max_map_token, show_progress)
        self.litellm_config: dict | None = None

    def config_litellm(self, api_key: str, model: str, base_url: str):
        self.litellm_config = {
            'api_key': api_key,
            'model': model,
            'base_url': base_url,
        }

    def get_map(
        self,
        depth: int | None = None,
        rel_dir_path: str | None = None,
        message_history: str = '',
    ) -> str:
        # t0 = time.time()
        ident2defrels, ident2refrels, identwrel2deftags, identwrel2reftags = (
            self.get_parsed_tags(
                rel_dir_path=rel_dir_path,
                depth=depth,
            )
        )

        llm_extracted_idents = extract_identifiers_from_text(
            message_history, self.litellm_config
        )

        defs_repr_with_prefix = self.get_definitions_tree(
            llm_extracted_idents, ident2defrels, identwrel2deftags
        )
        direct_refs_repr_with_prefix = self.get_references_tree(
            llm_extracted_idents, ident2refrels, identwrel2reftags
        )

        # print(f'Getting map took {time.time() - t0:.2f}s')
        result = (
            '\n'
            + defs_repr_with_prefix
            + direct_refs_repr_with_prefix
            + '\n'
            + Prompts.nav_only_reminder
        )
        # Control the maximum token count
        token_count = get_token_count_from_text(self.model_name, result)
        max_len = len(result) * self.max_map_token // token_count
        return result[:max_len]

    def get_parsed_tags(
        self,
        depth: int | None = None,
        rel_dir_path: str | None = None,
    ) -> tuple[dict, dict, dict, dict]:
        if rel_dir_path:
            all_abs_files = self.git_utils.get_absolute_tracked_files_in_directory(
                rel_dir_path=rel_dir_path,
                depth=depth,
            )
        else:
            all_abs_files = self.git_utils.get_all_absolute_tracked_files(depth=depth)

        ident2defrels = defaultdict(
            set
        )  # symbol identifier -> set of its definitions' relative file paths
        ident2refrels = defaultdict(
            list
        )  # symbol identifier -> list of its references' relative file paths
        identwrel2deftags = defaultdict(
            set
        )  # (relative file, symbol identifier) -> set of its DEF tags
        identwrel2reftags = defaultdict(
            set
        )  # (relative file, symbol identifier) -> set of its REF tags

        all_abs_files_iter = (
            tqdm(all_abs_files, desc='Parsing tags', unit='file')
            if self.show_progress
            else all_abs_files
        )
        for abs_file in all_abs_files_iter:
            rel_file = self.path_utils.get_relative_path_str(abs_file)
            parsed_tags = self.ts_parser.get_tags_from_file(abs_file, rel_file)

            for parsed_tag in parsed_tags:
                if parsed_tag.tag_kind == TagKind.DEF:
                    ident2defrels[parsed_tag.node_name].add(rel_file)
                    identwrel2deftags[(rel_file, parsed_tag.node_name)].add(parsed_tag)
                if parsed_tag.tag_kind == TagKind.REF:
                    ident2refrels[parsed_tag.node_name].append(rel_file)
                    identwrel2reftags[(rel_file, parsed_tag.node_name)].add(parsed_tag)

        return ident2defrels, ident2refrels, identwrel2deftags, identwrel2reftags

    def get_references_tree(
        self, llm_extracted_idents, ident2refrels, identwrel2reftags
    ):
        # Extract direct references for each identifier
        static_direct_refs = defaultdict(
            set
        )  # ExtractedIdent -> set of referenceing tags
        for ident_tup in llm_extracted_idents:
            mentioned_cls, mentioned_fn = (
                ident_tup.class_name,
                ident_tup.function_name,
            )
            if mentioned_fn:
                ref_rels = ident2refrels.get(mentioned_fn, set())
                ref_tags = set()
                for ref_rel in ref_rels:
                    ref_tags.update(
                        identwrel2reftags.get((ref_rel, mentioned_fn), set())
                    )
                static_direct_refs[ident_tup] = ref_tags
            elif mentioned_cls:
                ref_rels = ident2refrels.get(mentioned_cls, set())
                ref_tags = set()
                for ref_rel in ref_rels:
                    ref_tags.update(
                        identwrel2reftags.get((ref_rel, mentioned_cls), set())
                    )
                static_direct_refs[ident_tup] = ref_tags

        # Concatenate the direct references to another tree representation
        direct_refs_repr = ''
        for idx, (ident_tup, ref_tags) in enumerate(static_direct_refs.items()):
            mentioned_cls, mentioned_fn = (
                ident_tup.class_name,
                ident_tup.function_name,
            )
            direct_refs_repr += (
                f"\n{idx + 1}. References to '{mentioned_fn or mentioned_cls}':\n"
            )
            # Sort the tags by file path and line number
            ref_tags_list = list(ref_tags)
            ref_tags_list.sort(key=lambda tag: (tag.rel_path, tag.start_line))
            direct_refs_repr += self.tag_list_to_tree(ref_tags_list)
            direct_refs_repr += '\n'

        return Prompts.direct_ref_prefix + direct_refs_repr

    def get_definitions_tree(
        self, llm_extracted_idents, ident2defrels, identwrel2deftags
    ):
        # Extract definitions for each identifier
        static_defs = defaultdict(set)
        for ident_tup in llm_extracted_idents:
            mentioned_cls, mentioned_fn, mentioned_rel_file = (
                ident_tup.class_name,
                ident_tup.function_name,
                ident_tup.rel_file_name,
            )
            if mentioned_fn:
                def_rels = ident2defrels.get(mentioned_fn, set())
                def_tags = set()
                for def_rel in def_rels:
                    if mentioned_rel_file and mentioned_rel_file not in def_rel:
                        continue
                    def_tags.update(
                        identwrel2deftags.get((def_rel, mentioned_fn), set())
                    )
                static_defs[ident_tup] = def_tags
            elif mentioned_cls:
                def_rels = ident2defrels.get(mentioned_cls, set())
                def_tags = set()
                for def_rel in def_rels:
                    if mentioned_rel_file and mentioned_rel_file not in def_rel:
                        continue
                    def_tags.update(
                        identwrel2deftags.get((def_rel, mentioned_cls), set())
                    )
                static_defs[ident_tup] = def_tags

        # Concatenate the definitions to another tree representation
        defs_repr = ''
        for idx, (ident_tup, def_tags) in enumerate(static_defs.items()):
            mentioned_cls, mentioned_fn, mentioned_rel_file = (
                ident_tup.class_name,
                ident_tup.function_name,
                ident_tup.rel_file_name,
            )
            defs_repr += (
                f"\n{idx + 1}. Definitions of '{mentioned_fn or mentioned_cls}':\n"
            )
            # Sort the tags by file path and line number
            def_tags_list = list(def_tags)
            def_tags_list.sort(key=lambda tag: (tag.rel_path, tag.start_line))
            defs_repr += self.tag_list_to_tree(def_tags_list)
            defs_repr += '\n'

        return Prompts.def_prefix + defs_repr


if __name__ == '__main__':
    strategy = DirectRefStrategy(root='/home/ryan/django')
    print(
        strategy.get_map_with_token_count(
            message_history="""Model.get_FOO_display() does not work correctly with inherited choices. Description (last modified by Mariusz Felisiak) Given a base model with choices A containing 3 tuples Child Model inherits the base model overrides the choices A and adds 2 more tuples get_foo_display does not work correctly for the new tuples added Example: class A(models.Model): foo_choice = [("A","output1"),("B","output2")] field_foo = models.CharField(max_length=254,choices=foo_choice) class Meta: abstract = True class B(A): foo_choice = [("A","output1"),("B","output2"),("C","output3")] field_foo = models.CharField(max_length=254,choices=foo_choice) Upon invoking get_field_foo_display() on instance of B , For value "A" and "B" the output works correctly i.e. returns "output1" / "output2" but for value "C" the method returns "C" and not "output3" which is the expected behaviour"""
        )
    )
