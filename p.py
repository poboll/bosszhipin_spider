import asyncio, random
from pyppeteer import launch
from lxml import etree
import pandas as pd
import requests
import openpyxl


class ss_xz(object):
    def __init__(self):
        self.data_list = list()

    def screen_size(self):
        """使用tkinter获取屏幕大小"""
        import tkinter
        tk = tkinter.Tk()
        width = tk.winfo_screenwidth()
        height = tk.winfo_screenheight()
        tk.quit()
        return width, height

    # width, height = 1366, 768
    async def main(self):
        try:
            browser = await launch(headless=False,userDataDir="C:/Users/86150/Desktop/py配置文件",
                                   args=['--disable-infobars', '--window-size=1366,768', '--no-sandbox'])

            page = await browser.newPage()
            width, height = self.screen_size()
            await page.setViewport({'width': width, 'height': height})
            await page.goto(
                'https://www.zhipin.com/fuzhou/?ka=city-sites-101230100')
            await page.evaluateOnNewDocument(
                '''() =>{ Object.defineProperties(navigator, { webdriver: { get: () => false } }) }''')
            await asyncio.sleep(5)
            # 查询数据分析岗位
            await page.type(
                '#wrap > div.column-search-panel > div > div > div.search-form > form > div.search-form-con > p > input',
                '测试工程师', {'delay': self.input_time_random() - 50})
            await asyncio.sleep(2)
            # 点击搜索
            await page.click('#wrap > div.column-search-panel > div > div > div.search-form > form > button')
            await asyncio.sleep(5)


            # print(await page.content())
            # 获取页面内容
            i = 0
            while True:
                await asyncio.sleep(2)
                content = await page.content()
                html = etree.HTML(content)
                # 解析内容
                self.parse_html(html)
                # 翻页
                await page.click('#wrap > div.page-job-wrapper > div.page-job-inner > div > div.job-list-wrapper > div.search-job-result > div > div > div > a:nth-child(10)')
                await asyncio.sleep(3)
                i += 1
                print(i)
                # boss直聘限制翻页为10页，分省分批次抓取
                if i >= 10:
                    break
            df = pd.DataFrame(self.data_list)
            # df['职位'] = df.职位.str.extract(r'[(.*?)]', expand=True)
            df.to_excel('C:/Users/86150/Desktop/测试工程师-福州.xlsx', index=False)
            print(df)

        except Exception as a:
            print(a)


    def input_time_random(self):
        return random.randint(100, 151)

    def parse_html(self, html):

        li_list = html.xpath('//div[@class="search-job-result"]//ul[@class="job-list-box"]/li')
        data_df = []
        for li in li_list:
            # 获取文本
            items = {}
            items['职位'] = li.xpath('.//span[@class="job-name"]/text()')[0]
            items['薪酬'] = li.xpath('.//div[@class="job-info clearfix"]/span/text()')[0]
            items['公司名称'] = li.xpath('.//div[@class="company-info"]//h3/a/text()')[0]
            items['工作经验'] = li.xpath('.//div[@class="job-info clearfix"]/ul/li/text()')[0]
            items['学历要求'] = li.xpath('.//div[@class="job-info clearfix"]/ul/li/text()')[1]
            items['地区'] = li.xpath('.//span[@class="job-area"]/text()')[0]
            items['福利'] = li.xpath('.//div[@class="info-desc"]/text()')
            span_list = li.xpath('.//div[@class="job-card-footer clearfix"]/ul[@class="tag-list"]')
            for span in span_list:
                items['技能要求'] = span.xpath('./li/text()')
            ul_list = li.xpath('.//ul[@class="company-tag-list"]')
            for ul in ul_list:
                items['公司类型及规模'] = ul.xpath('./li/text()')
            xl_list = li.xpath('.//div[@class="job-info clearfix"]/ul[@class="company-tag-list"]')
            for xl in xl_list:
                items['工作经验及学历要求'] = xl.xpath('./li/text()')
            self.data_list.append(items)


    def run(self):
        asyncio.get_event_loop().run_until_complete(self.main())


if __name__ == '__main__':

    comment = ss_xz()
    comment.run()

