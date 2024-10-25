import math
from collections import Counter, defaultdict

import networkx as nx
from tqdm import tqdm

from locify.indexing.full_map.strategy import FullMapStrategy
from locify.indexing.prompts import Prompts
from locify.tree_sitter.parser import ParsedTag, TagKind


class RepoMapStrategy(FullMapStrategy):
    def __init__(
        self,
        model_name='gpt-4o',
        root='./',
        max_map_token=1024 * 3,
        content_prefix=Prompts.repo_content_prefix,
    ) -> None:
        super().__init__(model_name, root, max_map_token, content_prefix)

    def get_ranked_tags(
        self,
        depth: int | None = None,
        rel_dir_path: str | None = None,
        mentioned_rel_files: set | None = None,
        mentioned_idents: set | None = None,
    ) -> list[ParsedTag]:
        if rel_dir_path:
            all_abs_files = self.git_utils.get_absolute_tracked_files_in_directory(
                rel_dir_path=rel_dir_path,
                depth=depth,
            )
        else:
            all_abs_files = self.git_utils.get_all_absolute_tracked_files(depth=depth)
        num_files = len(all_abs_files)
        if mentioned_rel_files is None:
            mentioned_rel_files = set()
        if mentioned_idents is None:
            mentioned_idents = set()

        ident2defrels = defaultdict(
            set
        )  # symbol identifier -> set of its definitions' relative file paths
        ident2refrels = defaultdict(
            list
        )  # symbol identifier -> list of its references' relative file paths
        identwrel2tags = defaultdict(
            set
        )  # (relative file, symbol identifier) -> set of its tags
        personalization_dict = {}
        personalization_val = 100 / num_files

        for abs_file in tqdm(all_abs_files, desc='Parsing tags', unit='file'):
            rel_file = self.path_utils.get_relative_path_str(abs_file)

            if rel_file in mentioned_rel_files:
                personalization_dict[rel_file] = personalization_val

            parsed_tags = self.ts_parser.get_tags_from_file(abs_file, rel_file)

            for parsed_tag in parsed_tags:
                if parsed_tag.tag_kind == TagKind.DEF:
                    ident2defrels[parsed_tag.node_name].add(rel_file)
                    identwrel2tags[(rel_file, parsed_tag.node_name)].add(parsed_tag)
                if parsed_tag.tag_kind == TagKind.REF:
                    ident2refrels[parsed_tag.node_name].append(rel_file)

        all_idents = set(ident2defrels.keys()).intersection(set(ident2refrels.keys()))

        G = nx.MultiDiGraph()
        for ident in all_idents:
            defining_rel_files = ident2defrels[ident]
            if ident in mentioned_idents:
                multiplier = 10
            else:
                multiplier = 1

            for referencing_rel_file, num_refs in Counter(ident2refrels[ident]).items():
                for defining_rel_file in defining_rel_files:
                    num_refs = int(
                        math.sqrt(num_refs)
                    )  # Scale down the number of references
                    G.add_edge(
                        referencing_rel_file,
                        defining_rel_file,
                        weight=num_refs * multiplier,
                        identifier=ident,
                    )

        pers_kwargs = {}
        if personalization_dict:
            pers_kwargs = {
                'personalization': personalization_dict,
                'dangling': personalization_dict,
            }

        pagerank_scores = nx.pagerank(G, **pers_kwargs)

        identwrel2score: dict[tuple[str, str], float] = defaultdict(float)
        for src_rel_file in G.nodes:
            src_file_rank = pagerank_scores[src_rel_file]
            total_weight = sum(
                [data['weight'] for _, _, data in G.out_edges(src_rel_file, data=True)]
            )
            for _, dst_rel_file, data in G.out_edges(src_rel_file, data=True):
                ident = data['identifier']
                weight = data['weight']
                score = src_file_rank * weight / total_weight
                identwrel2score[(dst_rel_file, ident)] += score
        sorted_identwrel2score = sorted(
            identwrel2score.items(), key=lambda x: x[1], reverse=True
        )

        ranked_tags: list[ParsedTag] = []
        for (rel_file, ident), score in sorted_identwrel2score:
            # print(f"{score:.03f} {rel_file} {ident}")
            ranked_tags.extend(identwrel2tags.get((rel_file, ident), []))

        rel_files_with_no_tags = set(
            self.path_utils.get_relative_path_str(abs_file)
            for abs_file in all_abs_files
        )
        rel_files_has_tags = set(tag.rel_path for tag in ranked_tags)

        for src_rel_file, _ in pagerank_scores.items():
            if src_rel_file in rel_files_has_tags:
                rel_files_with_no_tags.remove(src_rel_file)
            if src_rel_file not in rel_files_has_tags:
                ranked_tags.append(
                    ParsedTag(  # Add a dummy tag for files with no tags
                        tag_kind=TagKind.DEF,
                        node_name='NO_NAME',
                        rel_path=src_rel_file,
                        abs_path=self.path_utils.get_absolute_path_str(src_rel_file),
                        start_line=-1,
                    )
                )

        # Note: Sort the tags by file path and line number can destroy the pagerank order
        # ranked_tags.sort(key=lambda tag: (tag.rel_path, tag.start_line))
        return ranked_tags
