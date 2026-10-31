/* Python ↔ React：JSON-RPC 2.0 over QWebChannel */

type Resolver = { resolve: (value: any) => void; reject: (error: Error) => void };

let seq = 0;
const pending = new Map<number, Resolver>();

function fire(event: string, detail: unknown): void {
  window.dispatchEvent(new CustomEvent(event, { detail }));
}

export function initBridge(): Promise<void> {
  return new Promise((resolve, reject) => {
    const QWebChannel = (window as any).QWebChannel;
    if (typeof QWebChannel === 'undefined') {
      reject(new Error('QWebChannel not loaded'));
      return;
    }
    new QWebChannel((window as any).qt.webChannelTransport, (channel: any) => {
      (window as any).__bridge = channel.objects.bridge;

      (window as any).__veinResult = (rawId: string | number, ok: boolean, payload: any) => {
        const id = Number(rawId);
        const entry = pending.get(id);
        if (!entry) return;
        pending.delete(id);
        if (ok) entry.resolve(payload);
        else entry.reject(new Error(String(payload ?? 'RPC failed')));
      };

      (window as any).__veinProgress = (taskId: string, done: number, total: number) =>
        fire('vein:progress', { taskId, done, total });

      (window as any).__veinLog = (line: string) => fire('vein:log', String(line));
      (window as any).__veinNotify = (title: string, message: string) =>
        fire('vein:notify', { title, message });
      (window as any).__veinNavigate = (page: string) => fire('vein:navigate', String(page));

      resolve();
    });
  });
}

export function rpc<T>(method: string, args: unknown[] = []): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const bridge = (window as any).__bridge;
    if (!bridge) {
      reject(new Error('Bridge not ready'));
      return;
    }
    const id = ++seq;
    pending.set(id, { resolve, reject });
    bridge.call(String(id), JSON.stringify({ jsonrpc: '2.0', id, method, params: { args } }));
  });
}

export function on<T>(event: string, handler: (detail: T) => void): () => void {
  const listener = (e: Event) => handler((e as CustomEvent).detail as T);
  window.addEventListener(event, listener);
  return () => window.removeEventListener(event, listener);
}
