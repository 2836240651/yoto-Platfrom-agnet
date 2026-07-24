"""Operator-facing UI — task templates, not free-form AI chat."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from langchain_core.messages import HumanMessage

from agent.graph import build_graph

st.set_page_config(page_title="运营助手", page_icon="📊", layout="wide")
st.title("运营助手")
st.caption("选择任务模板，填写参数，一键执行")

TASKS = {
    "抖音词分析": {
        "skill": "douyin-keyword-research",
        "fields": ["种子词"],
        "defaults": {"种子词": "渔具"},
        "prompt_tpl": "分析抖音种子词【{种子词}】的热搜词和潜力词",
    },
}

task_name = st.selectbox("选择任务", list(TASKS.keys()))
task = TASKS[task_name]

params = {}
cols = st.columns(2)
for i, field in enumerate(task["fields"]):
    with cols[i % 2]:
        params[field] = st.text_input(field, value=task["defaults"].get(field, ""))

confirmed = st.checkbox("我已确认参数无误")
run = st.button("开始执行", type="primary", disabled=not confirmed)

if run:
    prompt = task["prompt_tpl"].format(**params)
    with st.spinner("执行中，请稍候..."):
        graph = build_graph()
        result = graph.invoke(
            {"messages": [HumanMessage(content=prompt)]},
            config={"configurable": {"thread_id": f"ui-{task_name}"}},
        )
    st.success("完成")
    st.text_area("结果", value=result.get("final_answer", ""), height=300)

with st.expander("历史任务（TODO）"):
    st.info("后续接入 checkpoint 查询与任务列表")
