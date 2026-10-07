
## worker 层（backend/application/agent_runtime/worker）

### 日常两条命令
# 审查整层（7 类规则：语法/头序/argv/env污染/重名/注入四件套/NameError）
python3 -m backend.application.agent_runtime.worker.worker_audit

# 零磁盘工业级测试
TMPD="$(mktemp -d /dev/shm/t-XXXXXX)"; TMPDIR="$TMPD" \
  python3 -m backend.tests.industrial.run 2>&1 | grep -E "小计|总计|结果|FAIL"; \
  rm -rf "$TMPD"

### 不变量
A. worker_main.py 头序 = docstring → __future__ → 其它 import
   ❌ 禁止模块级写 os.environ
B. pool._is_worker_process 只读 env，不读 argv
C. worker_process.start() 四件套：
   env = dict(os.environ); env["LOCO_WORKER_ACTIVE"]="1"
   env["LOCO_WORKER_POOL_SIZE"]="0"; Popen(..., env=env)
D. 新增能力 → 新文件 + worker_bootstrap 注册，不动 5 件套
E. 任何 .py 改动 → 先过 worker_audit 再跑测试。编译过 ≠ 运行不炸
F. 审查器误报 → 改审查器，不改被审文件


## 硬件限制 · LLM 切模型速度（2026-09-26 定稿）

### 物理事实
- GPU：NVIDIA 8188 MiB 显存
- 两个 7B 模型（qwen3:8b ~4.7G + qwen2.5-coder:7b ~4.7G）无法共存
- 切模型必触发「卸载旧的 + 加载新的」= 6~12s 冷启动
- 这是显存物理限制，软件无法绕过

### 已落地的软件优化
| # | 优化 | 位置 | 效果 |
|---|------|------|------|
| 1 | keep_alive="30m" | backend/providers/implementations/ollama_provider.py | 同模型 30min 内不卸载 |
| 2 | httpx 单例共享（20 连接池） | 同上 | 第 2 次调用 68ms |
| 3 | 连接池 keepalive_expiry=30s | 同上 | TCP 层复用 |

### 实测基线（2026-09-26）
- qwen3:8b 连续 3 次：8633ms → 2462ms → 2350ms（稳定 2.4s）
- 切 qwen2.5-coder:7b：6652ms → 68ms（第 2 次秒回）
- 切回 qwen3:8b：11796ms → 2146ms

### 不要尝试的优化（都无效）
- 换 httpx 参数 / keep-alive 调大 → 硬件限制
- 启动预热所有模型 → 显存不够，会挤掉当前模型
- 多进程内预热 → 与主进程争抢显存
- 连接池调更大 → 68ms 已是 TCP 下限

### 前端体验补偿
- 切模型后 8s 内显示提示：「首次调用该模型预计 6~12s」
- 位置：frontend/src/features/agent_workspace/ui/agent_workspace_view.tsx（showModelWarmupHint）

### 若未来升级硬件
- 显存 ≥16GB → 两模型可共存 → 切换 <300ms
- 需重跑基线，更新此文档

## Electron 前端热更新（2026-09-26 定稿）

### 架构
- Windows Electron 生产模式：**远程优先 + 本地兜底**
- 远程：`http://<后端>:9022/app/`（后端挂载 `frontend/dist`）
- 本地兜底：`win-unpacked/dist/index.html`（离线用）
- 后端静态服务：`backend/api/static_frontend.py` → `/app`

### 日常开发（改前端 · 不重打）
1. `cd frontend && npm run build`
2. `cd .. && bash scripts/start_backend.sh`
3. Windows 端 Electron 按 F5

### 何时才需要重打 Electron（仅这 3 类）
- `desktop/electron/main.cjs`
- `desktop/electron/preload.cjs`
- `desktop/electron/ipc/*.cjs`
- `package.json`（electron 配置）

### 打包命令（仅上述场景）
- Linux：`cd frontend && npm run build:win:customer`
- 产物：`frontend/release/0.0.0/win-unpacked/`
- 压缩：`tar -czf pkg.tar.gz win-unpacked/`（370M → ~150M）
- 上传 Windows → 解压 → 双击 exe

### 首次启动 Windows 前置
- 后端在跑：`curl http://<linux_ip>:9022/app/`
- 防火墙放行 9022
- Windows 与 Linux 同网段

### 验证走没走远程
- Electron 打开后按 F12
- Console 里看 `[remote-first] loaded:` 或 `[remote-first] fallback to local dist`
