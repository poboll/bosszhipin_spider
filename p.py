import argparse
import asyncio
import os
import random
import sys
from pathlib import Path

import pandas as pd
from lxml import etree
from pyppeteer import launch
from pyppeteer.errors import TimeoutError as PyppeteerTimeoutError


DEFAULT_CITY = "fuzhou"
DEFAULT_CITY_CODE = "101230100"
DEFAULT_KEYWORD = "测试工程师"
DEFAULT_OUTPUT = "jobs.xlsx"
DEFAULT_TIMEOUT = 30

SEARCH_INPUT_SELECTORS = (
    "input[name='query']",
    "input.ipt-search",
    "#wrap .search-form input[type='text']",
)
SEARCH_BUTTON_SELECTORS = (
    "button.btn-search",
    "button[ka='search_box_index']",
    "form.search-form button[type='submit']",
)
JOB_CARD_XPATHS = (
    "//ul[contains(concat(' ', normalize-space(@class), ' '), ' job-list-box ')]/li",
    "//li[contains(concat(' ', normalize-space(@class), ' '), ' job-card-wrapper ')]",
    "//li[contains(concat(' ', normalize-space(@class), ' '), ' company-job-item ')]",
)
JOB_CARD_SELECTORS = (
    "ul.job-list-box > li",
    "li.job-card-wrapper",
    "li.company-job-item",
)
NEXT_PAGE_SELECTORS = (
    "a[ka*='page_next']",
    "a[aria-label='下一页']",
    "a.next",
    ".page a.next",
    ".ui-pagination-next:not(.disabled)",
    ".pagination-next:not(.disabled)",
)


class CrawlerError(RuntimeError):
    """Expected, actionable crawler failure."""


class SecurityVerificationRequired(CrawlerError):
    """BOSS requires the user to complete a security verification."""


def _clean_text(value):
    if hasattr(value, "xpath"):
        value = value.xpath("string(.)")
    return " ".join(str(value).split()).strip()


def _text_values(node, xpaths):
    values = []
    for xpath in xpaths:
        for value in node.xpath(xpath):
            text = _clean_text(value)
            if text and text not in values:
                values.append(text)
    return values


def _first_text(node, xpaths, default=""):
    values = _text_values(node, xpaths)
    return values[0] if values else default


def find_chrome_executable():
    """Return a common local Chrome path, or None for Pyppeteer's fallback."""
    candidates = [
        os.environ.get("CHROME_BIN"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    return None


class BossZhipinSpider:
    def __init__(
        self,
        city=DEFAULT_CITY,
        city_code=DEFAULT_CITY_CODE,
        keyword=DEFAULT_KEYWORD,
        output=DEFAULT_OUTPUT,
        max_pages=10,
        headless=True,
        executable_path=None,
        user_data_dir=None,
        timeout=DEFAULT_TIMEOUT,
        wait_for_verification=False,
    ):
        self.city = city
        self.city_code = city_code
        self.keyword = keyword
        self.output = Path(output).expanduser()
        self.max_pages = max_pages
        self.headless = headless
        self.executable_path = executable_path or find_chrome_executable()
        self.user_data_dir = str(Path(user_data_dir).expanduser()) if user_data_dir else None
        self.timeout = timeout
        self.wait_for_verification = wait_for_verification
        self.data_list = []

    @property
    def city_url(self):
        return f"https://www.zhipin.com/{self.city}/?ka=city-sites-{self.city_code}"

    async def _page_text(self, page):
        try:
            return await page.evaluate("() => document.body ? document.body.innerText : ''")
        except Exception:
            return ""

    async def _ensure_not_verification(self, page):
        url = page.url.lower()
        body = await self._page_text(page)
        markers = (
            "安全验证",
            "当前 ip 地址可能存在异常访问行为",
            "请完成验证",
            "异常访问行为",
        )
        if "/verify" not in url and not any(marker in body.lower() for marker in markers):
            return

        if self.wait_for_verification and not self.headless:
            print("检测到 BOSS直聘安全验证，请在浏览器窗口中完成验证。")
            deadline = asyncio.get_running_loop().time() + max(self.timeout, 120)
            while asyncio.get_running_loop().time() < deadline:
                await asyncio.sleep(1)
                url = page.url.lower()
                body = await self._page_text(page)
                if "/verify" not in url and not any(
                    marker in body.lower() for marker in markers
                ):
                    return

        raise SecurityVerificationRequired(
            "BOSS直聘要求完成安全验证。请使用 --headful --wait-for-verification，"
            "本脚本不会自动绕过验证。"
        )

    async def _wait_for_selector(self, page, selectors, description):
        deadline = asyncio.get_running_loop().time() + self.timeout
        while asyncio.get_running_loop().time() < deadline:
            await self._ensure_not_verification(page)
            for selector in selectors:
                try:
                    element = await page.querySelector(selector)
                    if element:
                        await element.dispose()
                        return selector
                except Exception:
                    continue
            await asyncio.sleep(0.5)
        raise CrawlerError(f"等待{description}超时；页面可能已改版或需要安全验证。")

    async def _launch_browser(self):
        args = [
            "--disable-infobars",
            "--window-size=1440,900",
            "--no-sandbox",
            "--disable-extensions",
            "--disable-component-extensions-with-background-pages",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-blink-features=AutomationControlled",
        ]
        options = {
            "headless": self.headless,
            "args": args,
            "defaultViewport": {"width": 1440, "height": 900},
        }
        if self.executable_path:
            options["executablePath"] = self.executable_path
        if self.user_data_dir:
            Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)
            options["userDataDir"] = self.user_data_dir
        return await launch(**options)

    async def _prepare_page(self, page):
        await page.evaluateOnNewDocument(
            """() => {
                Object.defineProperty(navigator, 'webdriver', { get: () => false });
            }"""
        )
        await page.setViewport({"width": 1440, "height": 900})
        try:
            await page.goto(
                self.city_url,
                waitUntil="domcontentloaded",
                timeout=self.timeout * 1000,
            )
        except PyppeteerTimeoutError as exc:
            await self._ensure_not_verification(page)
            raise CrawlerError(f"打开 BOSS直聘页面超时: {self.city_url}") from exc
        await self._wait_for_selector(page, SEARCH_INPUT_SELECTORS, "搜索输入框")

    async def _search(self, page):
        input_selector = await self._wait_for_selector(
            page, SEARCH_INPUT_SELECTORS, "搜索输入框"
        )
        button_selector = await self._wait_for_selector(
            page, SEARCH_BUTTON_SELECTORS, "搜索按钮"
        )
        await page.click(input_selector)
        await page.type(
            input_selector,
            self.keyword,
            {"delay": random.randint(50, 100)},
        )
        try:
            await asyncio.gather(
                page.click(button_selector),
                page.waitForNavigation(
                    {"waitUntil": "domcontentloaded", "timeout": self.timeout * 1000}
                ),
            )
        except PyppeteerTimeoutError:
            # Some BOSS layouts update the list asynchronously instead of navigating.
            pass
        await asyncio.sleep(2)
        await self._ensure_not_verification(page)
        await self._wait_for_selector(
            page,
            SEARCH_INPUT_SELECTORS + JOB_CARD_SELECTORS,
            "搜索结果页面",
        )

    def parse_html(self, html):
        """Parse known BOSS job-card layouts into the historical output columns."""
        rows = []
        seen = set()
        for xpath in JOB_CARD_XPATHS:
            for item in html.xpath(xpath):
                marker = item.getroottree().getpath(item)
                if marker in seen:
                    continue
                seen.add(marker)

                position = _first_text(
                    item,
                    (
                        ".//span[contains(concat(' ', normalize-space(@class), ' '), ' job-name ')]",
                        ".//p[contains(concat(' ', normalize-space(@class), ' '), ' name ')]",
                        ".//*[contains(concat(' ', normalize-space(@class), ' '), ' job-title ')]",
                    ),
                )
                if not position:
                    continue

                legacy_requirements = _text_values(
                    item,
                    (
                        ".//div[contains(concat(' ', normalize-space(@class), ' '), ' job-info ')]//ul/li",
                    ),
                )
                current_requirements = _text_values(
                    item,
                    (
                        ".//p[contains(concat(' ', normalize-space(@class), ' '), ' job-text ')]/span",
                    ),
                )
                if len(legacy_requirements) >= 2:
                    experience, education = legacy_requirements[:2]
                elif len(current_requirements) >= 3:
                    experience, education = current_requirements[1:3]
                else:
                    experience = education = ""

                skills = _text_values(
                    item,
                    (
                        ".//ul[contains(concat(' ', normalize-space(@class), ' '), ' tag-list ')]/li",
                        ".//div[contains(concat(' ', normalize-space(@class), ' '), ' tag-list ')]//li",
                    ),
                )
                company_tags = _text_values(
                    item,
                    (
                        ".//ul[contains(concat(' ', normalize-space(@class), ' '), ' company-tag-list ')]/li",
                    ),
                )
                rows.append(
                    {
                        "职位": position,
                        "薪酬": _first_text(
                            item,
                            (
                                ".//div[contains(concat(' ', normalize-space(@class), ' '), ' job-info ')]/span",
                                ".//*[contains(concat(' ', normalize-space(@class), ' '), ' salary ')]",
                            ),
                        ),
                        "公司名称": _first_text(
                            item,
                            (
                                ".//div[contains(concat(' ', normalize-space(@class), ' '), ' company-info ')]//h3/a",
                                ".//*[contains(concat(' ', normalize-space(@class), ' '), ' company-name ')]",
                            ),
                        ),
                        "工作经验": experience,
                        "学历要求": education,
                        "地区": _first_text(
                            item,
                            (
                                ".//span[contains(concat(' ', normalize-space(@class), ' '), ' job-area ')]",
                                ".//p[contains(concat(' ', normalize-space(@class), ' '), ' job-text ')]/span[1]",
                                ".//*[contains(concat(' ', normalize-space(@class), ' '), ' job-location ')]",
                            ),
                        ),
                        "福利": _text_values(
                            item,
                            (
                                ".//*[contains(concat(' ', normalize-space(@class), ' '), ' info-desc ')]",
                            ),
                        ),
                        "技能要求": skills,
                        "公司类型及规模": company_tags,
                        "工作经验及学历要求": [
                            value for value in (experience, education) if value
                        ],
                    }
                )
        self.data_list.extend(rows)
        return rows

    async def _find_next_selector(self, page):
        for selector in NEXT_PAGE_SELECTORS:
            try:
                handles = await page.querySelectorAll(selector)
                for handle in handles:
                    disabled = await handle.evaluate(
                        "element => element.classList.contains('disabled') "
                        "+ element.getAttribute('aria-disabled') === 'true'"
                    )
                    if not disabled:
                        for other in handles:
                            if other is not handle:
                                await other.dispose()
                        return handle, selector
                    await handle.dispose()
            except Exception:
                continue
        return None, None

    async def _next_page(self, page):
        handle, selector = await self._find_next_selector(page)
        if not handle:
            return False
        try:
            await handle.click()
            try:
                await page.waitForNavigation(
                    {"waitUntil": "domcontentloaded", "timeout": self.timeout * 1000}
                )
            except PyppeteerTimeoutError:
                pass
            await asyncio.sleep(2)
            await self._ensure_not_verification(page)
            await self._wait_for_selector(page, JOB_CARD_SELECTORS, "下一页结果")
            return True
        except Exception as exc:
            raise CrawlerError(f"点击下一页失败（选择器: {selector}）") from exc
        finally:
            await handle.dispose()

    async def main(self):
        browser = await self._launch_browser()
        try:
            page = await browser.newPage()
            await self._prepare_page(page)
            await self._search(page)

            for page_number in range(1, self.max_pages + 1):
                await self._wait_for_selector(page, JOB_CARD_SELECTORS, "职位列表")
                rows = self.parse_html(etree.HTML(await page.content()))
                print(f"第 {page_number} 页：提取 {len(rows)} 条")
                if page_number == self.max_pages or not await self._next_page(page):
                    break

            if not self.data_list:
                raise CrawlerError("页面未提取到职位数据；请检查关键词、地区或安全验证状态。")
            self.output.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(self.data_list).to_excel(self.output, index=False)
            print(f"已写入 {len(self.data_list)} 条数据：{self.output}")
            return len(self.data_list)
        finally:
            await browser.close()

    def run(self):
        return asyncio.run(self.main())


# Preserve the class name used by the original script for callers that imported it.
ss_xz = BossZhipinSpider


def build_parser():
    parser = argparse.ArgumentParser(description="抓取 BOSS直聘职位并导出 Excel")
    parser.add_argument("--city", default=DEFAULT_CITY, help="城市 slug，例如 fuzhou")
    parser.add_argument("--city-code", default=DEFAULT_CITY_CODE, help="城市编码")
    parser.add_argument("--keyword", default=DEFAULT_KEYWORD, help="职位关键词")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Excel 输出路径")
    parser.add_argument("--max-pages", type=int, default=10, help="最多抓取页数")
    parser.add_argument("--headful", action="store_true", help="显示浏览器窗口")
    parser.add_argument("--chrome", help="Chrome/Chromium 可执行文件路径")
    parser.add_argument("--user-data-dir", help="浏览器用户目录，用于保留人工验证后的会话")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="页面等待超时秒数")
    parser.add_argument(
        "--wait-for-verification",
        action="store_true",
        help="在可视浏览器中等待手动完成 BOSS 安全验证",
    )
    return parser


def cli(argv=None):
    args = build_parser().parse_args(argv)
    if args.max_pages < 1:
        print("--max-pages 必须大于 0", file=sys.stderr)
        return 2
    if args.timeout < 1:
        print("--timeout 必须大于 0", file=sys.stderr)
        return 2
    if args.wait_for_verification and not args.headful:
        print("--wait-for-verification 必须与 --headful 一起使用", file=sys.stderr)
        return 2
    if args.chrome and not Path(args.chrome).expanduser().is_file():
        print(f"Chrome 可执行文件不存在：{args.chrome}", file=sys.stderr)
        return 2
    try:
        BossZhipinSpider(
            city=args.city,
            city_code=args.city_code,
            keyword=args.keyword,
            output=args.output,
            max_pages=args.max_pages,
            headless=not args.headful,
            executable_path=args.chrome,
            user_data_dir=args.user_data_dir,
            timeout=args.timeout,
            wait_for_verification=args.wait_for_verification,
        ).run()
    except CrawlerError as exc:
        print(f"抓取失败：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
