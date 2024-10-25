# Copyright 2024 Superlinked, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from beartype.typing import Sequence
from typing_extensions import override

from superlinked.framework.common.dag.categorical_similarity_node import (
    CategoricalSimilarityNode,
)
from superlinked.framework.common.data_types import Vector
from superlinked.framework.common.interface.weighted import Weighted
from superlinked.framework.query.dag.query_embedding_node import QueryEmbeddingNode
from superlinked.framework.query.dag.query_node import QueryNode
from superlinked.framework.query.query_node_input import QueryNodeInput


class QueryCategoricalSimilarityNode(QueryEmbeddingNode[Vector, list[str]]):
    def __init__(
        self, node: CategoricalSimilarityNode, parents: Sequence[QueryNode]
    ) -> None:
        super().__init__(node, parents, list[str])

    @override
    def pre_process_node_input(
        self, node_inputs: Sequence[QueryNodeInput]
    ) -> Sequence[QueryNodeInput]:
        return [
            QueryCategoricalSimilarityNode.make_single_list_input(node_input)
            for node_input in node_inputs
        ]

    @staticmethod
    def make_single_list_input(node_input: QueryNodeInput) -> QueryNodeInput:
        if isinstance(node_input.value, list):
            return node_input
        return QueryNodeInput(
            Weighted([node_input.value.item], node_input.value.weight),
            node_input.to_invert,
        )