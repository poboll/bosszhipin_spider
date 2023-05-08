# Boss直聘数据爬取及数据可视化分析

## 1.数据的抓取

![](https://s2.loli.net/2023/05/08/6pMQDGP2u9ey4Rl.png)

采用的pyppeteer框架，对boss直聘上各大热门城市招聘信息，进行抓取，保存在excel中。

```python3
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
```

由于boss直聘限制翻页为10页，所以总共爬取了5100条信息用于分析，主要抓取的信息为职位，薪酬，地区，公司名称，公司类型，公司规模，福利及经验学历要求和技能要求。

![](https://s2.loli.net/2023/05/08/RZ9fYAhXxMOQDk5.png)



## 2.数据的清洗

从上面爬取的数据我们可以看到有很多垃圾数据，用pandas经过正则匹配，清洗后的数据如下图：

![](https://s2.loli.net/2023/05/08/92kvIWJEjpARizD.png)



## 3.可视化分析

本次使用帆软的FineBi进行数据可视化分析。将数据导入后如下图：

![](https://s2.loli.net/2023/05/08/jguZSs5YdrKbFel.png)

创建组件，来进行第一个分析：

1.发布岗位的地区分布图，主要为以下几个省的城市分岗位招聘信息，因为爬虫爬的数据有限，每个城市的岗位招聘信息大概290条左右：

![](https://s2.loli.net/2023/05/08/BQp92eOAfdaoJu4.png)

2.首先从公司类型的维度上进行分析，制作的职位数量与公司类型饼图如下，可以看出数据分析师岗位主要集中在互联网行业，电子商务以及教育和医疗行业。

![](https://s2.loli.net/2023/05/08/szvx2k74AZrLyUN.png)

3.从学历要求维度上分析，画出一下的饼图，可以看出数据分析师的岗位对学历的要求都是大专起步，本科占据了64.77%，硕士占比比较低。

![](https://s2.loli.net/2023/05/08/Nj3A5ibCkwBpZn7.png)

4.从工作年限要求来看，岗位主要分布在应届和3-5年经验，经验不限的占据大半这对应届生来说也是好消息。

![](https://s2.loli.net/2023/05/08/63Qnr42FptiR5lE.png)

5.从薪酬维度分析，可以从条形图看出10-15K的岗位占大部分，出现这种情况的原因大概两种，一种就是样本的数量太少了，刚好爬取的10-15k的岗位占据大多数，另一种一线城市的岗位薪资占据了大部分数据，不过不影响我们数据的展现。

![](https://s2.loli.net/2023/05/08/YsZG4UPiep3dJHL.png)

6.使用FineBi完成的整体仪表板图，如下：

![](https://s2.loli.net/2023/05/08/j5oExDfpqRZCPOT.png)

全部地区的岗位一览图

我们可以按照对应的省与城市进行联动，将数据细分到对应的省以及省下面的市区，由于爬取数量有限，都是几个热门城市的boss直聘网站的前10页信息，所以我们先从北上广深看看实时数据：

1.北京市数据

将鼠标点击左上角地图的北京市，就可以在整个仪表板页面显示北京的所有招聘信息，如下图：

![](https://s2.loli.net/2023/05/08/bfMcygFinr1SKCw.png)

从仪表板看数据一目了然，一线城市北京对数据分析师的学历要求90%都要求本科学历，工作经验50%的要求3-5年，薪资分布也是在10-15K以上。

我们在界面上依次点击学历要求为本科，工作经验为1-3年，然后数据就可以看到我们在北京市，学历要求为本科，工作经验为1-3年的数据。

北京市-本科学历-工作经验1-3年

基本在一线城市，起薪都是10K起步，还是很有吸引力的。

2.上海市的数据

同样将鼠标点击左上角地图的上海市，就可以显示上海市的情况了：

![](https://s2.loli.net/2023/05/08/gncHXTL9iBQY5pO.png)

3.广州市

![](https://s2.loli.net/2023/05/08/OlVmRUgqWho2DuB.png)

我们可以清晰的看出，一线城市相同岗位，学历要求有一定差别的，薪资差不多相同。

接下来看看新一线城市：

4.成都

![](https://s2.loli.net/2023/05/08/CrIbAyZNUxwSMoX.png)

5.武汉

![](https://s2.loli.net/2023/05/08/hBkNTyJIU7sjgtb.png)

6.杭州

![](https://s2.loli.net/2023/05/08/ETZ1cbwJyPjNl3q.png)

从上图仪表板我们可以看到，非一线城市薪资相对北上广有了很大幅度的降低，5-10K的岗位比较多，对学历的要求也更低，这可能是数据分析师这个行业也算最近几年火起来的行业，在一线城市的岗位毕竟多，机会也多，新一线城市未来几年的发展会更大的偏向。



## 4.技能要求词云图展示

我们上面唯一漏掉的数据就是技能要求的分析，可以用pandas将技能要求数据处理成一条一条的，然后用value_counts()函数计算每个词出现的频率。

附上词云图代码，当然你也可以FineBi绘制词云图：

```text
import pandas as pd
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from PIL import Image

def deal_excel():
    image = Image.open('C:/Users/Desktop/查找资料/2.jpg')  # 作为背景轮廓图
    graph = np.array(image)
    # 参数分别是指定字体、背景颜色、最大的词的大小、使用给定图作为背景形状
    wc = WordCloud(font_path='C:\Windows\Fonts\simsun.ttc', background_color='white', max_words=300, mask=graph)
    df = pd.read_excel('C:/Users/Desktop/职位数据呀呀.xlsx', sheet_name='Sheet2')
    df = df.loc[:, '技能要求'].value_counts()
    # print(df.head())
    # 将df转化成dataframe
    df = pd.DataFrame(df.reset_index())
    df.columns = ['技能要求', '数量']
    # 词
    name = list(df.技能要求)
    # 词的频率
    value = df.数量
    for i in range(len(name)):
        name[i] = str(name[i])
    # 词频以字典形式存储
    dic = dict(zip(name, value))
    # 根据给定词频生成词云
    wc.generate_from_frequencies(dic)
    plt.imshow(wc)
    # 不显示坐标轴
    plt.axis("off")
    plt.show()
    wc.to_file('词云图.png')  # 图片命名
    # 获取前10销量
    df = df.nlargest(10, '数量')
    print(df)


if __name__ == '__main__':
    deal_excel()
```