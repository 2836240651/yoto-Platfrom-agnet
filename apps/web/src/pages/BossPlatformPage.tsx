import { Link, useParams } from 'react-router-dom'

const PLATFORMS = [
  { id: 'douyin', name: '抖音', description: '内容电商运营数据' },
  { id: '1688', name: '1688', description: '货源与采购运营数据' },
  { id: 'temu', name: 'Temu', description: '跨境店铺运营数据' },
  { id: 'amazon', name: 'Amazon', description: '跨境店铺运营数据' },
] as const

type PlatformId = (typeof PLATFORMS)[number]['id']

function isPlatformId(value: string | undefined): value is PlatformId {
  return PLATFORMS.some((platform) => platform.id === value)
}

export function BossPlatformPage() {
  const { platform: platformId } = useParams()
  const platform = isPlatformId(platformId)
    ? PLATFORMS.find((item) => item.id === platformId)
    : undefined

  if (platform) {
    return (
      <section className="boss-page">
        <Link className="boss-back-link" to="/boss">← 返回平台运营数据</Link>
        <div className="boss-empty-state">
          <p className="boss-page-eyebrow">{platform.name}</p>
          <h1>{platform.name} 运营数据</h1>
          <p>该平台运营数据暂未接入。</p>
          <span>数据源接入后将在此展示。</span>
        </div>
      </section>
    )
  }

  return (
    <section className="boss-page">
      <div className="boss-page-header">
        <p className="boss-page-eyebrow">BOSS 视角</p>
        <h1>平台运营数据</h1>
        <p>选择一个平台查看运营数据接入状态。</p>
      </div>
      <div className="boss-platform-grid">
        {PLATFORMS.map((item) => (
          <Link key={item.id} className="boss-platform-card" to={`/boss/${item.id}`}>
            <span className="boss-platform-card__name">{item.name}</span>
            <span className="boss-platform-card__description">{item.description}</span>
            <span className="boss-platform-card__status">暂未接入数据</span>
          </Link>
        ))}
      </div>
    </section>
  )
}
