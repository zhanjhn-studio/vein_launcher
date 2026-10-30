/* Layui 2.13.9 接入（懒加载，不污染现有设计系统） */

const LAYUI_DIR = '../../../common/layui/layui-v2.13.9/layui';
const CSS_HREF = `${LAYUI_DIR}/css/layui.css`;

let cssLoaded = false;
let layerReady: Promise<any> | null = null;

function loadCss(): void {
  if (cssLoaded) return;
  cssLoaded = true;
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = CSS_HREF;
  link.dataset.layui = 'css';
  document.head.appendChild(link);
}

function waitForLayui(timeoutMs = 5000): Promise<any> {
  return new Promise((resolve, reject) => {
    const started = Date.now();
    const tick = () => {
      const layui = (window as any).layui;
      if (layui) {
        resolve(layui);
        return;
      }
      if (Date.now() - started > timeoutMs) {
        reject(new Error('layui 未加载'));
        return;
      }
      window.setTimeout(tick, 50);
    };
    tick();
  });
}

export function layuiVersion(): string {
  return (window as any).layui?.v ?? '未加载';
}

/** 懒加载 layui 的 layer 模块（首次调用才注入 CSS） */
export function getLayer(): Promise<any> {
  if (!layerReady) {
    layerReady = (async () => {
      const layui = await waitForLayui();
      loadCss();
      return new Promise<any>((resolve) => {
        layui.use('layer', () => resolve(layui.layer));
      });
    })();
  }
  return layerReady;
}

export async function layerMsg(text: string, icon = 1): Promise<void> {
  const layer = await getLayer();
  layer.msg(text, { icon, time: 1800 });
}

export async function layerConfirm(text: string): Promise<boolean> {
  const layer = await getLayer();
  return new Promise<boolean>((resolve) => {
    layer.confirm(text, { title: '确认', btn: ['确定', '取消'] }, (index: number) => {
      layer.close(index);
      resolve(true);
    }, () => resolve(false));
  });
}
