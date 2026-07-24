"""Mock report generator for M0 UI."""

from __future__ import annotations

from app.schemas.tasks import (
    AlertItem,
    KeywordCard,
    MetricItem,
    ReportCategories,
    ReportSummary,
    TaskReport,
)


def _card(
    keyword: str,
    priority: str,
    trend: str,
    reason: str,
    action: str,
) -> KeywordCard:
    return KeywordCard(
        keyword=keyword,
        priority=priority,  # type: ignore[arg-type]
        trend=trend,  # type: ignore[arg-type]
        reason=reason,
        metrics=[
            MetricItem(label="关联视频", value="86"),
            MetricItem(label="30天销量", value="1.2万"),
            MetricItem(label="增速", value="+32%"),
        ],
        evidence=["视频库样本", "近7天发片量上升"],
        action=action,
    )


def build_mock_report(seed: str, *, include_video: bool, include_product: bool) -> TaskReport:
  """Build a demo report tailored to seed keyword."""
  video_hot = [
      _card(f"{seed}装备", "P0", "up", "搜索热度高，带货视频集中", f"建议拍 3 条 #{seed}装备 话题片"),
      _card(f"专业{seed}", "P1", "flat", "热度稳定，竞争中等", "可作为副话题测试"),
  ] if include_video else []

  video_potential = [
      _card(f"碳素{seed}", "P0", "up", "周环比 +45%，新上榜", "本周优先测试内容"),
      _card(f"入门{seed}推荐", "P1", "up", "长尾词竞争低", "适合新号起量"),
  ] if include_video else []

  product_hot = [
      _card(f"{seed}套装", "P0", "up", "商品搜索量 Top 5", "可加大橱窗曝光"),
  ] if include_product else []

  product_potential = [
      _card(f"轻量化{seed}", "P1", "up", "销量增速高于品类均值", "适合上新测款"),
  ] if include_product else []

  all_cards = video_hot + video_potential + product_hot + product_potential
  p0_count = sum(1 for c in all_cards if c.priority == "P0")

  return TaskReport(
      summary=ReportSummary(
          keyword_count=len(all_cards),
          video_sample_count=66 if include_video else 0,
          product_sku_count=44 if include_product else 0,
          p0_count=p0_count,
      ),
      tags=[
          f"种子词：{seed}",
          "周期：近30天",
          "筛选：带货视频 + 商品搜索",
      ],
      alerts=[
          AlertItem(
              type="info",
              text=f"「{seed}」是主赛道种子词，差异化靠下方潜力词卡片，不要只盯种子词本身。",
          ),
          AlertItem(
              type="warn",
              text="热搜榜可能查不到部分长尾词，趋势请结合发片量与关联视频数判断。",
          ),
      ],
      categories=ReportCategories(
          video_hot=video_hot,
          video_potential=video_potential,
          product_hot=product_hot,
          product_potential=product_potential,
      ),
  )
