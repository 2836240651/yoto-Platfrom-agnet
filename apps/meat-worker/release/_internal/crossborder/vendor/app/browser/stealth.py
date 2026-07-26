"""降低 Playwright 自动化特征（Temu 对 webdriver 较敏感）"""

STEALTH_INIT_SCRIPT = """
(() => {
  const desc = (obj, key, val) => {
    try {
      Object.defineProperty(obj, key, { get: () => val, configurable: true });
    } catch (_) {}
  };
  desc(navigator, 'webdriver', undefined);
  if (!window.chrome) window.chrome = {};
  if (!window.chrome.runtime) {
    window.chrome.runtime = {
      connect: function() {
        return { onMessage: { addListener: function() {} }, postMessage: function() {} };
      },
      sendMessage: function() {},
    };
  }
  desc(navigator, 'languages', ['zh-CN', 'zh', 'en-US', 'en']);
  desc(navigator, 'plugins', [1, 2, 3, 4, 5]);
  const originalQuery = window.navigator.permissions.query;
  window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications'
      ? Promise.resolve({ state: Notification.permission })
      : originalQuery(parameters)
  );
})();
"""

BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-infobars",
    "--window-size=1280,900",
]

# Playwright 默认会带 --enable-automation，需剔除
IGNORE_DEFAULT_ARGS = ["--enable-automation"]
