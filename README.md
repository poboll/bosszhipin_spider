# BOSS直聘招聘数据抓取与分析

一个基于 Python、Pyppeteer 和 pandas 的 BOSS直聘招聘数据采集与分析项目。脚本按城市和职位关键词抓取公开职位卡片，导出 Excel，便于继续用 pandas 或 FineBI 做清洗和可视化。

> 这是一个三年前的个人项目。BOSS直聘页面结构和安全策略会变化，脚本会明确提示安全验证，不会自动绕过验证。请遵守目标网站的服务条款，控制请求频率，不要采集或传播不必要的个人信息。

## 功能

- 使用浏览器打开 BOSS直聘城市页面并搜索职位关键词。
- 兼容旧版 `job-list-box` 和当前常见职位卡片结构。
- 将职位、薪酬、公司、地区、经验、学历、福利、技能标签导出为 Excel。
- 合并目录中的多个 Excel 工作簿和工作表，并自动处理不同表头。
- 对页面改版、空数据、路径错误和安全验证给出明确错误。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `p.py` | BOSS直聘职位抓取 CLI |
| `q.py` | Excel 工作簿合并 CLI |
| `requirements.txt` | Python 依赖 |
| `environment.yml` | Conda 环境定义 |
| `tests/` | 解析和 Excel 合并回归测试 |
| `*.xlsx` | 历史抓取结果和分析数据，不是实时数据 |

## 安装

推荐使用 Python 3.11 的 Conda 环境：

```bash
conda env create -f environment.yml
conda activate bosszhipin_spider
```

也可以在已有 Conda 环境中安装：

```bash
conda activate bosszhipin_spider
python -m pip install -r requirements.txt
```

Pyppeteer 需要 Chrome 或 Chromium。脚本会自动寻找常见安装路径，也可以显式传入路径。例如 macOS：

```bash
--chrome "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

## 抓取职位

先用一页做小规模验证：

```bash
python p.py \
  --city fuzhou \
  --city-code 101230100 \
  --keyword "测试工程师" \
  --output output/jobs.xlsx \
  --max-pages 1 \
  --chrome "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

常用参数：

- `--city`：城市 URL slug，例如 `fuzhou`。
- `--city-code`：城市编码，例如福州 `101230100`。
- `--keyword`：职位或公司关键词。
- `--output`：Excel 输出路径。
- `--max-pages`：最多抓取页数，默认 10。
- `--headful`：显示浏览器窗口，适合首次运行或需要人工观察时使用。
- `--user-data-dir`：指定浏览器用户目录，以便在同一会话中保留人工验证结果。
- `--wait-for-verification`：与 `--headful` 一起使用，等待手动完成安全验证。

如果 BOSS直聘返回“安全验证”或提示当前 IP 存在异常访问，程序会退出并说明原因。可以在可视浏览器中重试：

```bash
python p.py --headful --wait-for-verification \
  --user-data-dir .browser-profile \
  --city fuzhou --city-code 101230100 \
  --keyword "测试工程师" --output output/jobs.xlsx --max-pages 1
```

## 合并 Excel

将一个目录下的工作簿和工作表合并为一个文件：

```bash
python q.py --input-dir . --output output/merged.xlsx
```

输出文件会自动从输入列表中排除，避免重复合并。合并后的字段包括：

`职位`、`薪酬`、`公司名称`、`工作经验`、`学历要求`、`地区`、`福利`、`技能要求`、`公司类型及规模`。

## 测试

```bash
python -m unittest discover -s tests -v
python p.py --help
python q.py --help
```

## 历史分析

项目最初使用抓取结果做了岗位地区、公司类型、学历、经验和薪酬分析，并在 FineBI 中制作仪表板。下面保留部分历史截图，截图中的数据不是实时数据。

![抓取结果](https://s2.loli.net/2023/05/08/6pMQDGP2u9ey4Rl.png)

![数据清洗](https://s2.loli.net/2023/05/08/92kvIWJEjpARizD.png)

![FineBI 仪表板](https://s2.loli.net/2023/05/08/j5oExDfpqRZCPOT.png)

![岗位地区分布](https://s2.loli.net/2023/05/08/BQp92eOAfdaoJu4.png)

![公司类型分析](https://s2.loli.net/2023/05/08/szvx2k74AZrLyUN.png)

![学历要求分析](https://s2.loli.net/2023/05/08/Nj3A5ibCkwBpZn7.png)

![工作经验分析](https://s2.loli.net/2023/05/08/63Qnr42FptiR5lE.png)

![薪酬分析](https://s2.loli.net/2023/05/08/YsZG4UPiep3dJHL.png)

![北京数据](https://s2.loli.net/2023/05/08/bfMcygFinr1SKCw.png)

![上海数据](https://s2.loli.net/2023/05/08/gncHXTL9iBQY5pO.png)

![广州数据](https://s2.loli.net/2023/05/08/OlVmRUgqWho2DuB.png)

![成都数据](https://s2.loli.net/2023/05/08/CrIbAyZNUxwSMoX.png)

![武汉数据](https://s2.loli.net/2023/05/08/hBkNTyJIU7sjgtb.png)

![杭州数据](https://s2.loli.net/2023/05/08/ETZ1cbwJyPjNl3q.png)

## Issue 与联系

仓库 Issue 是最合适的公开交流渠道。源码和运行说明都在本仓库中，提问时请附上操作系统、Python/Conda 版本、完整错误信息和脱敏后的页面状态，不要提交账号、Cookie 或验证码信息。
