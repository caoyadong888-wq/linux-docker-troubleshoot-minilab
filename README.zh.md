# Linux / Docker 排障最小样例

## 目的

在一台 Linux 上复现两类 Docker 故障，并用不改机器的方式把症状读出来：

1. 容器或 Compose 服务起不来（`container-wont-start`，进程直接退出），以及另一个服务能起来但健康检查失败、状态变为 unhealthy（`container-unhealthy`）。
2. 端口已经写在 Compose 里，但 curl 和 wget 访问 `127.0.0.1` 失败（`port-connectivity`），因为映射到了错误的容器端口。

`check/diagnose.sh` 读取 lab 文件，打印故障类别、探测地址和预期症状。默认是 `--dry-run`。它只打印报告，不写文件，也不启动 Docker。

## 输入

- 解压后的本包，工作目录就是包根目录。
- 带 bash 和 Python 3 的 Linux。
- 检查器需要 PyYAML（`python3 -m pip install -r requirements.txt`）。
- 要真正把 lab 拉起来时，需要 Docker Compose v2。只做 dry-run 时不需要守护进程。
- 故意写坏的场景文件：
  - `lab/01-container-wont-start/compose.yaml`
  - `lab/02-port-connectivity/compose.yaml`
- 修好的对照文件是同目录的 `compose.fixed.yaml`。

Lab 里的主机名是 `web-exits.lab.example.com`、`web-unhealthy.lab.example.com` 和 `web.lab.example.com`。发布端口是 `127.0.0.1:18081`、`127.0.0.1:18083` 和 `127.0.0.1:18082`。

## 步骤

1. `cd` 到包根目录（本文件所在目录）。
2. 先读 `lab/01-container-wont-start/EXPECTED.md` 和 `lab/02-port-connectivity/EXPECTED.md`。已安装 Docker Compose v2 时可以按 FIX 里的命令启动；也可以只做只读检查：

   ```bash
   bash check/diagnose.sh --dry-run
   ```

3. 运行检查器，把报告和 EXPECTED 对照。坏掉的 lab 退出码是 `2`。

   ```bash
   bash check/diagnose.sh
   ```

   不加参数时，模式仍然是 `--dry-run`。

4. 按各目录的 `FIX.md` 修改（或直接把修好的 `compose.fixed.yaml` 交给检查器），再跑一次：

   ```bash
   bash check/diagnose.sh --dry-run \
     --compose lab/01-container-wont-start/compose.fixed.yaml \
     --compose lab/02-port-connectivity/compose.fixed.yaml
   bash demo/run-demo.sh
   ```

   修好的文件退出码是 `0`。`demo/run-demo.sh` 会打印 `demo_result=OK`。

可选的现场启动命令写在每个 FIX 文件里，需要本机已有 Docker Compose v2。停止项目用 `docker compose -f <file> down`。

## 验收

跟着步骤做完后，在 `ACCEPTANCE.md` 里逐项打勾。完成标准：

- 两份 README 都写明目的、输入、步骤、验收、边界、要求。
- 场景 01 覆盖进程退出，以及容器变为 unhealthy。
- 场景 02 覆盖发布端口上 curl 和 wget 失败。
- `bash check/diagnose.sh` 默认 dry-run，输出里有 `writes=none`，并且不写宿主机文件。
- `bash demo/run-demo.sh` 退出码为 `0`，`demo/captured-output.txt` 与它的标准输出一致。
- `bash tests/run_tests.sh` 结束后，`tests/RESULTS.md` 末尾是 `FAILS=0`。
- 包内只使用 `example.com` 和 `127.0.0.1`，没有客户 IP、邮箱或密钥。

检查器退出码：

| 退出码 | 含义 |
| --- | --- |
| 0 | 选中的文件没有故障。 |
| 1 | 用法错误、文件读不了、live 目标被拒绝，或本机没有 Docker。 |
| 2 | 有故障。机器上的文件保持原样。 |

## 边界

- Lab 主机名使用 `*.example.com`，发布端口绑定 `127.0.0.1`。不要把样例指到生产主机，这些脚本也不修改生产配置。
- 示例镜像是公开的 Docker 官方镜像 `nginx:1.27-alpine`。本 lab 不要求付费镜像仓库，也不登录任何仓库。
- 检查脚本只把报告打到标准输出。不写 `/etc`、`/root`、`/home`、`/var`。不执行 `docker system prune`，也不执行 `docker system prune -a`，不删除镜像或数据卷。
- `--live` 需要显式打开。它最多执行 `docker compose ps`，以及针对 `http://127.0.0.1` 的 `curl`。其他探测地址会被拒绝。它不执行 `up`、`down`、`pull` 或 `rm`。
- 发现故障或用法错误时以非 0 退出，并且不改动机器。
- 默认是 dry-run，没有 Docker 的机器也可以跑完演示和测试。

## 要求

- Linux，以及 bash。
- Python 3.9 或更高，以及 PyYAML 6（见 `requirements.txt`）。
- 只有 FIX 文件里的可选启动步骤需要 Docker Engine 和 Docker Compose v2。安装方式以你的发行版和上游文档为准。
- 可选的 `--live` 端口探测和 FIX 示例使用 `curl`。`nginx:1.27-alpine` 镜像内的健康检查使用 `wget`。
- dry-run 不需要 root，检查器不调用 sudo。
- 真正启动 lab 时，本机端口 `18081`、`18082`、`18083` 需要空闲。

## 目录

- `README.md`、`README.zh.md` — 英文和中文说明
- `ACCEPTANCE.md` — 勾选清单
- `lab/01-container-wont-start/` — 坏掉的 Compose、修好的 Compose、EXPECTED、FIX
- `lab/02-port-connectivity/` — 坏掉的 Compose、修好的 Compose、EXPECTED、FIX
- `check/diagnose.sh`、`check/diagnose.py` — 只读检查，默认 dry-run
- `demo/run-demo.sh`、`demo/demo.md`、`demo/captured-output.txt` — 一次跑通的命令记录
- `tests/` — pytest、`run_tests.sh` 和 `RESULTS.md`
- `LICENSE` — MIT
- `CHANGELOG.md` — 1.0.0
- `requirements.txt` — PyYAML

## 快速开始

```bash
python3 -m pip install -r requirements.txt
bash check/diagnose.sh --dry-run
bash demo/run-demo.sh
bash tests/run_tests.sh
```

## 场景

### 01 · 容器起不来 / 不健康（`lab/01-container-wont-start/`）

- **故障现象**：`web-exits` 启动后立即退出，日志里有 nginx emerg，提示打不开 `/etc/nginx/broken.conf`。`web-unhealthy` 进程在运行，但 `docker compose ps` 显示 `unhealthy`。
- **诊断**：运行 `bash check/diagnose.sh --dry-run`，会报出 `container-wont-start` 和 `container-unhealthy`（`result=FAULT`，退出码 2）。详见 `EXPECTED.md`。
- **修复**：删掉错误的 `command:` 覆盖；把健康检查地址从 `/healthz` 改成 `http://127.0.0.1/`。见 `FIX.md` 和 `compose.fixed.yaml`。
- **验证**：运行 `bash check/diagnose.sh --dry-run --compose lab/01-container-wont-start/compose.fixed.yaml`，应得到 `faults=0`、`result=OK`，退出码 0。

### 02 · 端口不通（`lab/02-port-connectivity/`）

- **故障现象**：容器状态是 `Up`，但 `curl http://127.0.0.1:18082/` 被拒绝。
- **诊断**：映射 `127.0.0.1:18082:8080` 指向的端口在容器内没有进程监听（nginx 监听的是 80）。检查脚本报 `port-connectivity`。
- **修复**：把映射改成 `127.0.0.1:18082:80`。见 `FIX.md`。
- **验证**：运行 `bash check/diagnose.sh --dry-run --compose lab/02-port-connectivity/compose.fixed.yaml`，应得到 `faults=0`、`result=OK`；实际启动时 curl 退出码为 0。

## Paid help / 可付费协助

提供固定价的 Linux/Docker 远程排障，范围包括：容器起不来或不健康、端口/网络不通、Nginx 反代、Compose 配置、systemd 服务。

- **价格**：每个问题 ¥99–299（约 $30–$100），先看文字描述再报价。
- **方式**：文字沟通。你提供日志和配置（请先去掉密钥），我交付根因、修复步骤和验证方法。
- **联系**：caoyadong888@gmail.com（仅邮件）
