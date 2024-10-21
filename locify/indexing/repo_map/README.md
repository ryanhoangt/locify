# Aider's RepoMap Indexing Strategy

## Introduction

This strategy is inspired by [aider's
implementation](https://github.com/paul-gauthier/aider/blob/main/aider/repomap.py). It's similar to
the full map indexing strategy, but it's used PageRank as a heuristic to find methods/classes that
are most important/influential in the codebase, where the nodes are source files and the edges are
the references between methods/classes in the source files.
