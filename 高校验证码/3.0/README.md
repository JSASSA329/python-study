# 验证码滑块获取器 3.0 使用说明

## 程序架构
- 模块 `破解验证码.py`：封装一次获取与验证的流程函数 `fetch_once`，辅助函数 `resolve_login_js` 负责读取 `login.js`。
- 模块 `login.js`：生成请求所需的签名参数（`captchaKey`、`token`、`iv` 等），依赖 `crypto-js`。
- 模块 `ui.py`：PyQt5 图形界面，使用 `QThread` 后台执行批量任务，提供间隔时间、获取数量、保存目录输入，并实时展示日志。
- 依赖关系：`ui.py` 通过 `importlib` 动态加载 `破解验证码.py`，调用其 `fetch_once`；`fetch_once` 使用 `execjs` 编译并调用 `login.js` 以生成参数；`requests` 请求验证码接口；`ddddocr` 计算滑块匹配位置并提交验证。

## 运行环境与依赖
- Python：3.10 及以上（64 位环境推荐）
- Node.js：用于 `execjs` 执行 `login.js`
- Python 包：
  - `requests`
  - `PyQt5`
  - `pyexecjs`（包名：`execjs`）
  - `ddddocr`
- Node 包（在 3.0 目录执行）：
  - `crypto-js`

安装示例：
```bash
# 进入 3.0 目录
cd 盘符:\路径\路径\验证码滑块\高校验证码\3.0

# 安装 Python 依赖
pip install PyQt5 requests execjs ddddocr

# 安装 Node 依赖
npm i crypto-js
```

## 功能说明
- 间隔时间（秒）：支持小数，控制每次获取的时间间隔。
- 获取数量：设置本次批量获取的次数。
- 保存目录：固定路径保存图片；图片文件名为 `bg_<毫秒时间戳>.jpg`，避免覆盖。
- 日志输出：实时显示参数、响应、匹配结果与验证结果，便于观察与问题定位。

## 使用方法
### 图形界面（推荐）
1. 启动界面：
   ```bash
   python "盘符:\路径\路径\验证码滑块\高校验证码\3.0\ui.py"
   ```
2. 在界面中设置：
   - 间隔时间（秒）：如 `2.5`、`3`
   - 获取数量：如 `10`
   - 保存目录：选择或输入目标路径
3. 点击“开始”运行；日志会在下方实时显示。点击“停止”可中途结束。

### 命令行（批量循环）
- 直接运行 `破解验证码.py` 并指定循环间隔：
  ```bash
  python "盘符:\路径\路径\路径\高校验证码\3.0\破解验证码.py" --interval 2
  ```
- 未提供 `--interval` 时，程序会在命令行交互中提示输入秒数。

## 目录结构
```
3.0/
├─ 破解验证码.py     # 一次获取与验证流程（fetch_once/resolve_login_js）
├─ login.js          # 参数生成与签名（依赖 crypto-js）
├─ ui.py             # PyQt5 图形界面与后台线程
└─ __pycache__/      # Python 编译缓存
```

## 工作流程概览
- 获取验证码：调用 `get/verification/image` 接口，返回背景图与滑块图、`token`。
- 计算滑动距离：`ddddocr.slide_match` 返回目标位置坐标（含毫秒级时间戳命名的图片持久化）。
- 提交验证：调用 `check/verification/result` 接口，携带坐标与签名参数，返回 `result:true/false` 与 `validate` 信息。

## 常见问题
- 字体警告：控制台出现 `qt.qpa.fonts: Unable to enumerate family` 可忽略，不影响运行。
- 依赖缺失：如 `crypto-js` 未安装，`login.js` 的 `require('crypto-js')` 会报错；请在 3.0 目录执行 `npm i crypto-js`。
- 运行卡顿：日志过多可能影响 UI 流畅度，建议增大间隔或减少批量次数。

## 免责声明
- 本程序仅用于技术学习与研究，请勿用于任何违反网站服务条款或法律法规的用途。由此产生的风险与责任由使用者自行承担。