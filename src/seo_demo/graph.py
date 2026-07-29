"""StateGraph 装配:节点、边、入口。新增阶段 = 加一个节点,不改动既有节点。"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from . import nodes
from .state import WorkflowState


def build_graph():
    graph = StateGraph(WorkflowState)

    graph.add_node("serp_research", nodes.serp_research)
    graph.add_node("architecture", nodes.architecture)
    graph.add_node("write_article", nodes.write_article)
    graph.add_node("brand_rewrite", nodes.brand_rewrite)
    graph.add_node("audit", nodes.audit)
    graph.add_node("publish_prepare", nodes.publish_prepare)

    graph.set_entry_point("serp_research")
    graph.add_edge("serp_research", "architecture")
    graph.add_edge("architecture", "write_article")
    graph.add_edge("write_article", "brand_rewrite")
    graph.add_edge("brand_rewrite", "audit")
    graph.add_edge("audit", "publish_prepare")
    graph.add_edge("publish_prepare", END)

    return graph.compile()
