/* Python <-> React 通信桥（QWebChannel） */

let seq = 0;
const pending = new Map();

export function initBridge() {
  return new Promise((resolve, reject) => {
    if (typeof QWebChannel === 'undefined') {
      reject(new Error('QWebChannel 未加载'));
      return;
    }
    new QWebChannel(window.qt.webChannelTransport, (channel) => {
      window.__bridge = channel.objects.bridge;

      window.__veinResult = (id, ok, payload) => {
        const entry = pending.get(Number(id));
        if (!entry) return;
        pending.delete(Number(id));
        if (ok) entry.resolve(payload);
        else entry.reject(new Error(payload || '调用失败'));
      };

      window.__veinProgress = (taskId, downloaded, total) => {
        window.dispatchEvent(
          new CustomEvent('vein:progress', { detail: { taskId, downloaded, total } })
        );
      };

      window.__veinLog = (line) => {
        window.dispatchEvent(new CustomEvent('vein:log', { detail: String(line) }));
      };

      window.__veinNotify = (title, message) => {
        window.dispatchEvent(
          new CustomEvent('vein:notify', { detail: { title, message } })
        );
      };

      resolve();
    });
  });
}

export function call(method, ...args) {
  return new Promise((resolve, reject) => {
    if (!window.__bridge) {
      reject(new Error('桥未就绪'));
      return;
    }
    const id = ++seq;
    pending.set(id, { resolve, reject });
    window.__bridge.call(String(id), JSON.stringify({ method, args }));
  });
}
