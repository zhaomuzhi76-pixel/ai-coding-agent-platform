"""
会话级模型选择契约层。

职责边界（不可扩展）：
  - 描述"可被选择的模型"与"一次会话的四件套绑定"
  - 只做数据描述与自校验
  - 不持有注册表、不持有 IO、不做解析
上游：无
下游：providers.multimodal.contracts、rag.selection.contracts
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, FrozenSet, Mapping, Optional


class Modality(str, Enum):
    """模型可输入或可输出的模态。"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class ModelKind(str, Enum):
    """前端选择器分组。"""
    LLM = "llm"
    IMAGE_GEN = "image_gen"
    EMBEDDING = "embedding"
    RERANK = "rerank"


def _freeze_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(meta))


def _ensure_nonempty(value: str, field_name: str) -> None:
    if not value:
        raise ValueError(f"{field_name} must not be empty")


@dataclass(frozen=True)
class ModelDescriptor:
    """LLM / 图片生成模型描述，供前端下拉与能力门控共用。"""
    id: str
    provider: str
    kind: ModelKind
    input_modalities: FrozenSet[Modality]
    output_modalities: FrozenSet[Modality]
    display: str = ""
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", _freeze_meta(self.meta))
        _ensure_nonempty(self.id, "ModelDescriptor.id")
        _ensure_nonempty(self.provider, "ModelDescriptor.provider")

        if self.kind not in (ModelKind.LLM, ModelKind.IMAGE_GEN):
            raise ValueError(
                f"ModelDescriptor.kind must be LLM or IMAGE_GEN, got {self.kind!r}"
            )
        if not self.input_modalities:
            raise ValueError("ModelDescriptor.input_modalities must not be empty")
        if not self.output_modalities:
            raise ValueError("ModelDescriptor.output_modalities must not be empty")

        if self.kind is ModelKind.LLM and Modality.TEXT not in self.output_modalities:
            raise ValueError("LLM ModelDescriptor must output TEXT")
        if self.kind is ModelKind.IMAGE_GEN and Modality.IMAGE not in self.output_modalities:
            raise ValueError("IMAGE_GEN ModelDescriptor must output IMAGE")

    @property
    def display_name(self) -> str:
        return self.display or f"{self.id} · {self.provider}"

    def supports_input(self, modality: Modality) -> bool:
        return modality in self.input_modalities

    def supports_output(self, modality: Modality) -> bool:
        return modality in self.output_modalities


@dataclass(frozen=True)
class EmbeddingDescriptor:
    """向量模型描述。dim 参与索引命名空间隔离，必填。"""
    id: str
    provider: str
    dim: int
    display: str = ""
    max_input_tokens: int = 8192
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", _freeze_meta(self.meta))
        _ensure_nonempty(self.id, "EmbeddingDescriptor.id")
        _ensure_nonempty(self.provider, "EmbeddingDescriptor.provider")
        if self.dim <= 0:
            raise ValueError(f"EmbeddingDescriptor.dim must be > 0, got {self.dim}")
        if self.max_input_tokens <= 0:
            raise ValueError("EmbeddingDescriptor.max_input_tokens must be > 0")

    @property
    def display_name(self) -> str:
        return self.display or f"{self.id} · {self.provider}"


@dataclass(frozen=True)
class RerankDescriptor:
    """精排模型描述。"""
    id: str
    provider: str
    display: str = ""
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", _freeze_meta(self.meta))
        _ensure_nonempty(self.id, "RerankDescriptor.id")
        _ensure_nonempty(self.provider, "RerankDescriptor.provider")

    @property
    def display_name(self) -> str:
        return self.display or f"{self.id} · {self.provider}"


@dataclass(frozen=True)
class SelectionBinding:
    """
    会话级四件套绑定。
    None 表示"未选"，回退策略由上层 L3 负责，本层不做默认值填充。
    """
    llm_id: Optional[str] = None
    image_gen_id: Optional[str] = None
    embedding_id: Optional[str] = None
    rerank_id: Optional[str] = None

    def is_empty(self) -> bool:
        return (
            self.llm_id is None
            and self.image_gen_id is None
            and self.embedding_id is None
            and self.rerank_id is None
        )

    def with_llm(self, llm_id: str) -> "SelectionBinding":
        return SelectionBinding(
            llm_id=llm_id,
            image_gen_id=self.image_gen_id,
            embedding_id=self.embedding_id,
            rerank_id=self.rerank_id,
        )

    def with_image_gen(self, image_gen_id: Optional[str]) -> "SelectionBinding":
        return SelectionBinding(
            llm_id=self.llm_id,
            image_gen_id=image_gen_id,
            embedding_id=self.embedding_id,
            rerank_id=self.rerank_id,
        )

    def with_embedding(self, embedding_id: str) -> "SelectionBinding":
        return SelectionBinding(
            llm_id=self.llm_id,
            image_gen_id=self.image_gen_id,
            embedding_id=embedding_id,
            rerank_id=self.rerank_id,
        )

    def with_rerank(self, rerank_id: str) -> "SelectionBinding":
        return SelectionBinding(
            llm_id=self.llm_id,
            image_gen_id=self.image_gen_id,
            embedding_id=self.embedding_id,
            rerank_id=rerank_id,
        )
