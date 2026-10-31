/**
 * 极简 Lua 子集：只支持声明式 UI 需要的语法
 *   local x = expr
 *   return expr
 *   expr: 表构造、函数调用、字符串/数字/布尔、.. 拼接
 * 用法：evalLua(source, env) -> value
 */

const ALLOWED_TYPES = new Set([
  'panel', 'row', 'text', 'button', 'input', 'table', 'list', 'badge', 'image', 'divider',
]);

function tokenize(src) {
  const tokens = [];
  const n = src.length;
  let i = 0;
  while (i < n) {
    const c = src[i];
    if (/\s/.test(c)) { i += 1; continue; }
    if (c === '-' && src[i + 1] === '-') {
      while (i < n && src[i] !== '\n') i += 1;
      continue;
    }
    if (c === '"' || c === "'") {
      const quote = c;
      let j = i + 1;
      let out = '';
      while (j < n && src[j] !== quote) {
        if (src[j] === '\\' && j + 1 < n) { out += src[j + 1]; j += 2; continue; }
        out += src[j];
        j += 1;
      }
      tokens.push({ kind: 'string', value: out });
      i = j + 1;
      continue;
    }
    if (/[0-9]/.test(c)) {
      let j = i;
      while (j < n && /[0-9._]/.test(src[j])) j += 1;
      tokens.push({ kind: 'number', value: Number(src.slice(i, j).replace(/_/g, '')) });
      i = j;
      continue;
    }
    if (/[A-Za-z_]/.test(c)) {
      let j = i;
      while (j < n && /[A-Za-z0-9_]/.test(src[j])) j += 1;
      tokens.push({ kind: 'name', value: src.slice(i, j) });
      i = j;
      continue;
    }
    if (c === '.' && src[i + 1] === '.') { tokens.push({ kind: 'op', value: '..' }); i += 2; continue; }
    if ('{}=,().[]'.includes(c)) { tokens.push({ kind: 'op', value: c }); i += 1; continue; }
    if (c === ';') { i += 1; continue; }
    throw new Error(`Lua 子集不支持字符：${c}`);
  }
  return tokens;
}

function createParser(tokens) {
  let pos = 0;
  const peek = () => tokens[pos];
  const eat = (value) => {
    const t = tokens[pos];
    if (!t || t.value !== value) throw new Error(`期望 ${value}，实际 ${t ? t.value : 'EOF'}`);
    pos += 1;
    return t;
  };
  const accept = (value) => {
    const t = tokens[pos];
    if (t && t.value === value) { pos += 1; return true; }
    return false;
  };

  function parseTable() {
    eat('{');
    const obj = { __array: [] };
    while (!accept('}')) {
      if (accept('[')) {
        const key = parseExpr();
        eat(']');
        eat('=');
        obj[String(key)] = parseExpr();
      } else if (peek() && peek().kind === 'name' && tokens[pos + 1] && tokens[pos + 1].value === '=') {
        const key = tokens[pos].value;
        pos += 2;
        obj[key] = parseExpr();
      } else {
        obj.__array.push(parseExpr());
      }
      accept(',');
      accept(';');
    }
    return obj.__array.length ? { __array: obj.__array, ...obj } : obj;
  }

  function parsePrimary() {
    const t = tokens[pos];
    if (!t) throw new Error('表达式意外结束');
    if (t.value === '{') return parseTable();
    if (t.value === '(') { pos += 1; const v = parseExpr(); eat(')'); return v; }
    if (t.kind === 'string') { pos += 1; return t.value; }
    if (t.kind === 'number') { pos += 1; return t.value; }
    if (t.kind === 'name') {
      pos += 1;
      if (t.value === 'true') return true;
      if (t.value === 'false') return false;
      if (t.value === 'nil') return null;
      // 函数调用：name(.name)*(table|string)
      let value = t.value;
      let args = undefined;
      while (accept('.')) {
        const field = tokens[pos];
        pos += 1;
        value += `.${field.value}`;
      }
      if (peek() && (peek().value === '{' || peek().kind === 'string')) {
        args = parsePrimary();
      }
      return { __call: value, args };
    }
    throw new Error(`无法解析 token: ${t.value}`);
  }

  function parseConcat() {
    let left = parsePrimary();
    while (accept('..')) {
      const right = parsePrimary();
      left = `${resolveValue(left)}${resolveValue(right)}`;
    }
    return left;
  }

  function parseExpr() { return parseConcat(); }

  function parseChunk() {
    const statements = [];
    while (pos < tokens.length) {
      if (accept('local')) {
        const name = tokens[pos].value;
        pos += 1;
        eat('=');
        statements.push({ kind: 'local', name, expr: parseExpr() });
      } else if (accept('return')) {
        statements.push({ kind: 'return', expr: parseExpr() });
      } else {
        parseExpr();
      }
    }
    return statements;
  }

  return { parseChunk };
}

function resolveValue(value) {
  if (value && typeof value === 'object' && '__call' in value) throw new Error('未解析的调用');
  return value;
}

export function evalLua(source, builder) {
  const tokens = tokenize(source);
  const parser = createParser(tokens);
  const statements = parser.parseChunk();
  const env = new Map();

  const call = (path, args) => {
    const parts = path.split('.');
    const root = parts[0] === 'ui' ? builder : env.get(parts[0]);
    if (!root) throw new Error(`未知标识符：${parts[0]}`);
    let target = root;
    for (let i = 1; i < parts.length; i += 1) {
      target = target && target[parts[i]];
      if (!target) throw new Error(`未知函数：${path}`);
    }
    if (typeof target !== 'function') throw new Error(`不是函数：${path}`);
    return target(args === undefined ? {} : evaluate(args));
  };

  const evaluate = (expr) => {
    if (expr && typeof expr === 'object') {
      if ('__call' in expr) return call(expr.__call, expr.args);
      const out = {};
      for (const [key, value] of Object.entries(expr)) {
        if (key === '__array') continue;
        out[key] = evaluate(value);
      }
      if (Array.isArray(expr.__array) && expr.__array.length > 0) {
        const values = expr.__array.map(evaluate);
        const named = Object.keys(out);
        // 纯数组表（如 children = { ... }）直接返回数组
        if (named.length === 0) return values;
        out.children = values;
      }
      return out;
    }
    return expr;
  };

  let result = null;
  for (const stmt of statements) {
    if (stmt.kind === 'local') env.set(stmt.name, evaluate(stmt.expr));
    else if (stmt.kind === 'return') result = evaluate(stmt.expr);
  }
  return result;
}

export function sanitize(node, depth = 0) {
  if (depth > 12 || node == null) return null;
  if (typeof node === 'string' || typeof node === 'number' || typeof node === 'boolean') {
    return { type: 'text', props: { value: String(node) } };
  }
  if (typeof node !== 'object') return null;
  const type = String(node.type || '').toLowerCase();
  if (!ALLOWED_TYPES.has(type)) return null;
  const props = {};
  for (const [key, value] of Object.entries(node)) {
    if (key === 'children' || key === 'type') continue;
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      props[key] = value;
    }
  }
  const rawChildren = Array.isArray(node.children) ? node.children : [];
  return {
    type,
    props,
    children: rawChildren.map((c) => sanitize(c, depth + 1)).filter(Boolean),
  };
}

export function makeBuilder() {
  const builder = {};
  for (const type of ALLOWED_TYPES) {
    builder[type] = (props) => {
      const node = { type, ...(props || {}) };
      if (Array.isArray(props?.children)) node.children = props.children;
      return node;
    };
  }
  return builder;
}

export { ALLOWED_TYPES };
