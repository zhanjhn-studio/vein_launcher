"""设置页新增“界面自定义”区块（圆角 / 缩放 / 动效）。"""

from pathlib import Path

path = Path(r"Z:\Vein Launche\vein_launcher\presentation\webui\src\settingsPage.tsx")
t = path.read_text(encoding="utf-8")

if "uiCustom" not in t:
    t = t.replace("import { ACCENT_PRESETS, currentAccent } from './accent';",
                  "import { ACCENT_PRESETS, currentAccent } from './accent';\nimport { getUiCustom, setUiCustom } from './uiCustom';", 1)
    t = t.replace("  const [theme, setTheme] = useState<Theme>(currentTheme());",
                  "  const [theme, setTheme] = useState<Theme>(currentTheme());\n  const [uiC, setUiCState] = useState(getUiCustom());", 1)

    anchor = """            <div className="kv">
              <span>Language</span>"""
    block = """            <div className="setting-block">
              <div className="setting-label">界面自定义</div>
              <div className="kv" style={{ marginTop: 6 }}>
                <span>圆角</span>
                <b>
                  <select
                    value={uiC.radius}
                    onChange={(e) => {
                      setUiCustom({ radius: e.target.value as any });
                      setUiCState(getUiCustom());
                    }}
                  >
                    <option value="small">小</option>
                    <option value="medium">中</option>
                    <option value="large">大</option>
                  </select>
                </b>
              </div>
              <div className="kv">
                <span>界面缩放</span>
                <b>
                  <select
                    value={uiC.zoom}
                    onChange={(e) => {
                      setUiCustom({ zoom: e.target.value as any });
                      setUiCState(getUiCustom());
                    }}
                  >
                    <option value="95">95%</option>
                    <option value="100">100%</option>
                    <option value="105">105%</option>
                  </select>
                </b>
              </div>
              <div className="kv">
                <span>动效</span>
                <b>
                  <select
                    value={uiC.motion}
                    onChange={(e) => {
                      setUiCustom({ motion: e.target.value as any });
                      setUiCState(getUiCustom());
                    }}
                  >
                    <option value="on">开启</option>
                    <option value="off">关闭</option>
                  </select>
                </b>
              </div>
            </div>
""" + anchor
    assert anchor in t
    t = t.replace(anchor, block, 1)
    path.write_text(t, encoding="utf-8")
    print("settings custom section added")
