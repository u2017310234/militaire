import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import markdown
import cairosvg
import json
import time


def fetch_incremental_news(url,last_date):
    """Fetch news articles published after the given date."""
    
    news = []

    try:
        headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}
        print(url)
        response = requests.get(url, headers=headers)
        
        system_instruction='''
        #背景
        你是新闻编辑，熟悉在html中查找信息。
        #目标
        从html中找到{last_date}发布的新闻url。
        #要求
        1. 以列表格式输出
        2. 输入为空，或没有找到时，返回空列表
        3. 找全
        4. 引号用""
        5. 如果返回的url不全，你需要补全为完整的url（以http开头）
            #范例
            [
                "https://www.justice.gov/opa/pr/roofing-business-owner-and-payroll-administrator-sentenced-employment-tax-conspiracy",
                "https://www.justice.gov/opa/pr/pennsylvania-man-pleads-guilty-child-exploitation-crimes",
                "https://www.justice.gov/opa/pr/oklahoma-man-charged-operating-large-scale-dog-fighting-and-trafficking-venture"
            ]
            以下是输入：
            '''
        model = genai.GenerativeModel("gemini-2.5-pro")
        
        result = model.generate_content(system_instruction+":"+response.text)
        try:

            result1=result.text.replace('```json', '').replace('\n```', '').strip()
            print(result1)
            result2 = json.loads(result1)
        except:
            result1=result.text.replace('```json\n', '').replace('\n```', '').replace('```', '').strip()
            print(result1)
            result2 = json.loads(result1)
        
        return result2

    except requests.exceptions.RequestException as e:
        return ""
        
def generate_summary(content):
    """Generate a markdown summary using Gemini."""
    prompt =      '''  #背景
        你是新闻编辑，擅长总结新闻摘要，并提取相关信息。
        #目标
        根据输入，生成一篇新闻摘要。
        #要求
        1. 以中文输出 第一行为二级标题下的空格
        2. 需要包括日期、发布主体、新闻类别、英文标题和摘要
        3. 以markdown格式输出
        4. 摘要为六级标题（6个#）
        5. 新闻类别包括 制裁名单 规则变化 司法案例 
        6. 除此之外不要生成其它任何东西
        <范例>
        ##   
        # Treasury Targets Mexico-Based Leader of Transnational Criminal Organization Responsible for Smuggling Thousands of Migrants Across the U.S. Southern Border
        ###### 3月18日，美国财政部外国资产控制办公室（OFAC）根据行政令E.O.13581对洛佩斯人口走私组织（LopezHSO）的关键领导人Jumilca Sandivel实施制裁，将其纳入SDN名单。该组织总部设在危地马拉，负责从危地马拉通过墨西哥向美国走私数千名非法外国人，该组织已与2024年7月5日被纳入SDN名单；Hernandez Perez还与曾经负责杀害9名美国公民的暴力贩毒组织La Linea合作。同时，OFAC还发布了一项警报，提示与根据行政令E.O.14157被认定为恐怖组织的国际卡特尔有关的外国金融机构和其他实体的制裁风险。
        发布日期 2025年7月23日
        发布主体 美国财政部外国资产控制办公室OFAC
        新闻类别 司法案例
        </范例>
    '''
    model = genai.GenerativeModel("gemini-2.5-pro")
    result = model.generate_content(prompt+":"+content)

    return result.text

def generate_svg_cover(summary):
    """Generate an SVG cover image based on the summary."""
    svg_template = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="800" height="400">
        <rect width="800" height="400" fill="#f5f5f5"/>
        <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-size="24" fill="#333">
            {summary[:100]}...
        </text>
    </svg>
    """
    return svg_template

def save_svg_as_png(svg_content, output_path):
    """Convert SVG content to PNG and save."""
    cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to=output_path)



def main():
    # Determine the date range for incremental news
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    last_date = yesterday.strftime("%Y-%m-%d")
    print(last_date)
    # Fetch news
    urls = ["https://www.justice.gov/news/press-releases",
    "https://home.treasury.gov/news/press-releases",
    "https://www.fatf-gafi.org/en/publications.html",
    "https://ofac.treasury.gov/recent-actions",
    "https://aqygzj.mofcom.gov.cn/zhxx/"
]  # Updated news source
    news=[]
    try:
        for url in urls:
            new = fetch_incremental_news(url,last_date)
            time.sleep(1)
            try:
                news =news+new
            except:
                news=news+[new]
    except:
        print('error')

    # Process each news article
    try:
        for url in news:
            response = requests.get(url)
            #soup = BeautifulSoup(response.text, "html.parser")
            summary = generate_summary(response.text)
            content = summary.replace('```markdown\n', '').replace('\n```', '').strip()+'\n\n'
            
            # Save summary as markdown
            md_filename = f"/work/日报/{last_date}.md"
            with open(md_filename, "a", encoding="utf-8") as md_file:
                md_file.write(content)


        #notion
        headers = {
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28' 
        }

        chunk_size = 5000
        for i in range(0, len(content), chunk_size):
            content_notion = notion_json(content[i:i+chunk_size])
            requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(content_notion))
            print(i)

            
    except:
        print('error')        
    a='''# Generate and save SVG cover
        svg_content = generate_svg_cover(summary)
        svg_filename = f"{article['title'][:50].replace(' ', '_')}.svg"
        png_filename = f"{article['title'][:50].replace(' ', '_')}.png"
        with open(svg_filename, "w", encoding="utf-8") as svg_file:
            svg_file.write(svg_content)
        save_svg_as_png(svg_content, png_filename)
        '''
if __name__ == "__main__":
    main()
