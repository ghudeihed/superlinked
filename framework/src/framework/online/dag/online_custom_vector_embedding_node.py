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

from beartype.typing import cast
from typing_extensions import override

from superlinked.framework.common.dag.context import ExecutionContext
from superlinked.framework.common.dag.custom_node import CustomVectorEmbeddingNode
from superlinked.framework.common.dag.node import Node
from superlinked.framework.common.data_types import Vector
from superlinked.framework.common.exception import ValidationException
from superlinked.framework.common.interface.has_length import HasLength
from superlinked.framework.common.parser.parsed_schema import ParsedSchema
from superlinked.framework.common.storage_manager.storage_manager import StorageManager
from superlinked.framework.common.transform.transform import Step
from superlinked.framework.common.transform.transformation_factory import (
    TransformationFactory,
)
from superlinked.framework.online.dag.evaluation_result import EvaluationResult
from superlinked.framework.online.dag.online_node import OnlineNode


class OnlineCustomVectorEmbeddingNode(
    OnlineNode[CustomVectorEmbeddingNode, Vector], HasLength
):
    def __init__(
        self,
        node: CustomVectorEmbeddingNode,
        parents: list[OnlineNode],
        storage_manager: StorageManager,
    ) -> None:
        super().__init__(node, parents, storage_manager)
        self._embedding_transformation = (
            TransformationFactory.create_embedding_transformation(
                self.node.transformation_config
            )
        )

    @property
    @override
    def length(self) -> int:
        return self.node.length

    @property
    def embedding_transformation(self) -> Step[Vector, Vector]:
        return self._embedding_transformation

    @override
    def evaluate_self(
        self,
        parsed_schemas: list[ParsedSchema],
        context: ExecutionContext,
    ) -> list[EvaluationResult[Vector]]:
        return [self.evaluate_self_single(schema, context) for schema in parsed_schemas]

    def evaluate_self_single(
        self,
        parsed_schema: ParsedSchema,
        context: ExecutionContext,
    ) -> EvaluationResult[Vector]:
        if len(self.parents) == 0:
            result = self.load_stored_result(parsed_schema.id_, parsed_schema.schema)
            if result is None:
                result = Vector.init_zero_vector(self.node.length)
        else:
            input_: EvaluationResult[list[float]] = cast(
                OnlineNode[Node[Vector], list[float]], self.parents[0]
            ).evaluate_next_single(parsed_schema, context)
            input_value = input_.main.value
            self._validate_input_value(input_value)
            result = self.embedding_transformation.transform(
                Vector(input_value), context
            )
        return EvaluationResult(self._get_single_evaluation_result(result))

    def _validate_input_value(self, input_value: list[float]) -> None:
        if len(input_value) != self.length:
            raise ValidationException(
                f"{self.class_name} can only process `Vector` inputs"
                + f" of size {self.length}"
                + f", got {len(input_value)}"
            )
