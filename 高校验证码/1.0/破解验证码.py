"""
[实现内容]：python实现手机验证码滑块破解

链接地址:'https://authserver.whsw.cn/'

[环境使用]:
    python 3.10
    pycharm

[模块使用]:
    requests -> pip install requests
    execjs -> pip install pyexecjs
    ddddocr -> pip install ddddocr
"""

# 接口:'https://captcha.chaoxing.com/captcha/get/verification/image?callback=cx_captcha_function&captchaId=qDG21VMg9qS5Rcok4cfpnHGnpf5LhcAv&type=slide&version=1.1.20&captchaKey=795c162d5f6b3e859107ec1768cf9b1b&token=6b14db4710aa90eb52bc0a225e1b2cd4%3A1763398779116&referer=https%3A%2F%2Fauthserver.whsw.cn%2Fcas%2Flogin%3Fservice%3Dhttps%253A%252F%252Fauthserver.whsw.cn%252Flogin&iv=b1182c99a5d3e1ee474ea79467e19e70&_=1763398484773'
# 关键字搜索: 'captchaKey'

# 导入数据请求模块
import requests
# 导入执行js代码模块
import execjs
# 导入时间模块
import time
# 导入正则表达式模块
import re
# 导入识别验证码模块
from ddddocr import DdddOcr
# 读取js代码文件
js_file = open('login.js', encoding='utf-8').read()
# 编译js代码文件
js_code = execjs.compile(js_file)
# 模拟浏览器
headers = {
    'connection': 'keep-alive',
    'host': 'captcha.chaoxing.com',
    'sec-fetch-dest': 'script',
    'referer': 'https://authserver.whsw.cn/',
    # 'sec-fetch-mode': 'no-cors',
    # 'sec-fetch-site': 'cross-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0'
}

# 验证码信息接口
url = 'https://captcha.chaoxing.com/captcha/get/verification/image'
# 获取当前时间戳
_ = int(time.time() * 1000)
# 查询参数
params = js_code.call('get_params', _)
print(params)

# 把时间戳添加到参数中
params['_'] = _
# 发送请求，获取响应的文本数据
text = response = requests.get(url=url, params=params, headers=headers).text
print(text)

# 提取验证码的图片
bg_img, slide_img = re.findall('"shadeImage":"(.*?)","cutoutImage":"(.*?)"', text)[0]
# 提取token值
token = re.findall('"token":"(.*?)"', text)[0]
print(bg_img, slide_img)
print(token)

"""获取验证码滑动距离"""
# 获取图片数据内容
bg_content = requests.get(bg_img, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0'}).content
with open('bg.jpg', 'wb') as f:
    f.write(bg_content)
slide_content = requests.get(slide_img, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0'}).content
# 识别距离
resp = DdddOcr(det=False, ocr=True, show_ad=False).slide_match(bg_content, slide_content, simple_target=True)
print(resp)

# 获取滑动距离
x = resp.get('target')[0]
"""识别验证码"""
# 识别接口
link = 'https://captcha.chaoxing.com/captcha/check/verification/result'
# 查询参数
link_params = {
    'callback': 'cx_captcha_function',
    'captchaId': 'qDG21VMg9qS5Rcok4cfpnHGnpf5LhcAv',
    'type': 'slide',
    'token': token,
    'textClickArr': '[{"x":%d}]' % x,
    'coordinate': '[]',
    'runEnv': '10',
    'version': '1.1.20',
    't': 'a',
    'iv': params['iv'],
    '_': int(time.time() * 1000)
}
# 发送请求，获取响应的文本数据
link_text = requests.get(link, params=link_params, headers=headers).text
print(link_text)