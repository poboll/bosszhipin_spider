import unittest

from lxml import etree

from p import BossZhipinSpider


JOB_HTML = """
<main>
  <ul class="job-list-box">
    <li class="job-card-wrapper">
      <span class="job-name">测试工程师</span>
      <div class="job-info clearfix">
        <span>10-15K</span>
        <ul><li>1-3年</li><li>本科</li></ul>
      </div>
      <div class="company-info"><h3><a>示例科技</a></h3></div>
      <span class="job-area">福州·鼓楼区</span>
      <div class="info-desc">双休，五险一金</div>
      <div class="job-card-footer clearfix"><ul class="tag-list"><li>Python</li><li>自动化测试</li></ul></div>
      <ul class="company-tag-list"><li>互联网</li><li>100-499人</li></ul>
    </li>
    <li class="company-job-item">
      <a class="job-info">
        <div class="job-info-top">
          <p class="name">数据分析师</p>
          <p class="salary">15-25K</p>
        </div>
        <p class="job-text"><span>福州·仓山区</span><span>经验不限</span><span>大专</span></p>
        <p class="company-name">另一家科技</p>
      </a>
    </li>
  </ul>
</main>
"""


class SpiderParserTests(unittest.TestCase):
    def test_parse_supports_legacy_and_current_job_cards(self):
        spider = BossZhipinSpider(keyword="测试工程师")

        rows = spider.parse_html(etree.HTML(JOB_HTML))

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["职位"], "测试工程师")
        self.assertEqual(rows[0]["薪酬"], "10-15K")
        self.assertEqual(rows[0]["公司名称"], "示例科技")
        self.assertEqual(rows[0]["技能要求"], ["Python", "自动化测试"])
        self.assertEqual(rows[1]["职位"], "数据分析师")
        self.assertEqual(rows[1]["地区"], "福州·仓山区")
        self.assertEqual(rows[1]["工作经验"], "经验不限")
        self.assertEqual(rows[1]["学历要求"], "大专")

    def test_parse_ignores_non_job_list_items(self):
        spider = BossZhipinSpider(keyword="测试工程师")

        rows = spider.parse_html(etree.HTML("<main><div>no jobs</div></main>"))

        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
