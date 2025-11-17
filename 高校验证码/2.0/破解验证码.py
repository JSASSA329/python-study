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

import requests
import execjs
import time
import re
import argparse
import sys
from pathlib import Path
from ddddocr import DdddOcr

def fetch_once(js_code, headers):
    url = 'https://captcha.chaoxing.com/captcha/get/verification/image'
    ts = int(time.time() * 1000)
    params = js_code.call('get_params', ts)
    print(params)
    params['_'] = ts
    text = requests.get(url=url, params=params, headers=headers).text
    print(text)
    bg_img, slide_img = re.findall('"shadeImage":"(.*?)","cutoutImage":"(.*?)"', text)[0]
    token = re.findall('"token":"(.*?)"', text)[0]
    print(bg_img, slide_img)
    print(token)
    bg_content = requests.get(bg_img, headers={'User-Agent': headers['User-Agent']}).content
    with open(f'bg_{ts}.jpg', 'wb') as f:
        f.write(bg_content)
    slide_content = requests.get(slide_img, headers={'User-Agent': headers['User-Agent']}).content
    resp = DdddOcr(det=False, ocr=True, show_ad=False).slide_match(bg_content, slide_content, simple_target=True)
    print(resp)
    x = resp.get('target')[0]
    link = 'https://captcha.chaoxing.com/captcha/check/verification/result'
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
    link_text = requests.get(link, params=link_params, headers=headers).text
    print(link_text)

def resolve_login_js():
    base = Path(__file__).resolve().parent
    candidates = [base / 'login.js', base.parent / 'login.js']
    for p in candidates:
        if p.exists():
            return p.read_text(encoding='utf-8')
    raise FileNotFoundError('login.js not found')

def ask_interval_seconds():
    while True:
        try:
            s = input('请勿将此程序用于非法用途，只做参考学习，请输入轮询时长(秒)：').strip()
            val = float(s)
            if val <= 0:
                print('时长必须大于0')
                continue
            return val
        except Exception:
            print('请输入有效的数字(支持小数)')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=float, default=None)
    args = parser.parse_args()
    js_code = execjs.compile(resolve_login_js())
    headers = {
        'connection': 'keep-alive',
        'host': 'captcha.chaoxing.com',
        'sec-fetch-dest': 'script',
        'referer': 'https://authserver.whsw.cn/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0'
    }
    interval = args.interval if args.interval is not None else ask_interval_seconds()
    print(f'定时运行，每次间隔 {interval} 秒')
    while True:
        try:
            fetch_once(js_code, headers)
        except Exception as e:
            print(e, file=sys.stderr)
        time.sleep(interval)

if __name__ == '__main__':
    main()