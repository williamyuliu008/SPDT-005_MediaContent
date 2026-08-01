# -*- coding: utf-8 -*-
"""
magazine — 科学杂志生成器模块包
===================================

子模块：
  magazine_blueprint   选题策划器
  magazine_orchestrator 管線编排器
  magazine_assembler   产品组装器

快捷入口：
  from platform.2_structure.magazine import load_blueprint, MagazineOrchestrator, MagazineAssembler
"""

from .magazine_blueprint import (
    MagazineSpec,
    ArticleSpec,
    MagazineBlueprint,
    MagazineBlueprintLoader,
    MagazineBlueprintGenerator,
    load_blueprint,
)

from .magazine_orchestrator import (
    MagazineOrchestrator,
    MagazineRunResult,
    ArticleRunResult,
)

from .magazine_assembler import (
    MagazineAssembler,
    MagazineArtifact,
)

__all__ = [
    "MagazineSpec",
    "ArticleSpec",
    "MagazineBlueprint",
    "MagazineBlueprintLoader",
    "MagazineBlueprintGenerator",
    "load_blueprint",
    "MagazineOrchestrator",
    "MagazineRunResult",
    "ArticleRunResult",
    "MagazineAssembler",
    "MagazineArtifact",
]
