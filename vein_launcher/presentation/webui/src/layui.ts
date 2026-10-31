/* Layui 2.13.9 接入：vendor 加载 + 模块化调用
 * 设计原则：默认不注入 layui.css，避免其全局Reset影响现有 React 设计；
 * 仅在真正使用 layui 组件（layer/form/element 等）时按需加载样式。
 */

const LAYUI_BASE = 'vendor/layui';
const CSS_HREF = `${LAYUI_BASE}/css/layui.css`;

let cssLoading: Promise<void> | null = null;
const moduleCache = new Map<string, Promise<any>>();

export function layuiVersion(): string {
  const layui = (window as any).layui;
  return layui?.v ? String(layui.v) : '未加载';
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
        reject(new Error('layui.js 未加载（检查 vendor/layui/layui.js）'));
        return;
      }
      window.setTimeout(tick, 50);
    };
    tick();
  });
}

/** 注入 layui.css（幂等，只在首次使用组件时调用） */
export function loadLayuiCss(): Promise<void> {
  if (cssLoading) return cssLoading;
  cssLoading = new Promise<void>((resolve, reject) => {
    if (document.querySelector('link[data-layui="css"]')) {
      resolve();
      return;
    }
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = CSS_HREF;
    link.dataset.layui = 'css';
    link.onload = () => resolve();
    link.onerror = () => reject(new Error(`layui.css Load failed：${CSS_HREF}`));
    document.head.appendChild(link);
  });
  return cssLoading;
}

/** 按模块使用 layui，例如 useLayui('layer') / useLayui('form') */
export async function useLayui(module: 'layer' | 'form' | 'element' | 'table' | 'dropdown' | 'util'): Promise<any> {
  const cached = moduleCache.get(module);
  if (cached) return cached;

  const task = (async () => {
    await loadLayuiCss();
    const layui = await waitForLayui();
    return new Promise<any>((resolve) => {
      layui.use(module, () => resolve(layui[module]));
    });
  })();

  moduleCache.set(module, task);
  return task;
}

export async function layerMsg(text: string, icon = 1): Promise<void> {
  const layer = await useLayui('layer');
  layer.msg(text, { icon, time: 1800 });
}

export async function layerConfirm(text: string): Promise<boolean> {
  const layer = await useLayui('layer');
  return new Promise<boolean>((resolve) => {
    layer.confirm(text, { title: 'Confirm', btn: ['OK', 'Cancel'] }, (index: number) => {
      layer.close(index);
      resolve(true);
    }, () => resolve(false));
  });
}

/** Open a layui layer（page 类型），用于承载表单/表格等 layui 组件 */
export async function layerOpen(title: string, html: string, width = '560px', height = '420px'): Promise<void> {
  const layer = await useLayui('layer');
  layer.open({
    type: 1,
    title,
    area: [width, height],
    shadeClose: true,
    className: 'vl-layer',
    content: html,
  });
}

/** Component preview：验证 layer + form + element + table 是否可用 */
export async function openLayuiPreview(): Promise<void> {
  const html = `
    <div style="padding:16px">
      <form class="layui-form">
        <div class="layui-form-item">
          <label class="layui-form-label">昵称</label>
          <div class="layui-input-block">
            <input type="text" name="name" lay-verify="required" placeholder="layui Form component"
                   autocomplete="off" class="layui-input">
          </div>
        </div>
        <div class="layui-form-item">
          <label class="layui-form-label">开关</label>
          <div class="layui-input-block">
            <input type="checkbox" name="enable" lay-skin="switch" lay-text="Enable|停用" checked>
          </div>
        </div>
        <div class="layui-form-item">
          <div class="layui-input-block">
            <button class="layui-btn" lay-submit>提交</button>
            <button type="reset" class="layui-btn layui-btn-primary">Reset</button>
          </div>
        </div>
      </form>
      <table class="layui-table" lay-size="sm">
        <thead><tr><th>模块</th><th>Status</th></tr></thead>
        <tbody>
          <tr><td>layer</td><td>可用</td></tr>
          <tr><td>form</td><td>可用</td></tr>
          <tr><td>element</td><td>可用</td></tr>
        </tbody>
      </table>
    </div>`;
  await layerOpen('Layui Component preview', html);
}
